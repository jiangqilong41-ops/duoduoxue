# 真机同步流程

## 目录

- [1. 预检](#1-预检)
- [2. 静止数据库](#2-静止数据库)
- [3. 拉取与合并](#3-拉取与合并)
- [4. 写回与回读](#4-写回与回读)
- [5. 增量写后失败分类](#5-增量写后失败分类)
- [6. 启动与清理](#6-启动与清理)
- [Release 例外](#release-例外)

## 1. 预检

在仓库根目录创建仅当前用户可访问的临时工作目录。设备操作、校验或 launch 失败时保留并报告其绝对路径；只有最终成功或确认 no-op 后才尝试删除，删除失败时报告残留绝对路径：

```bash
work=$(mktemp -d "${TMPDIR:-/tmp}/duoduoxue-course-sync.XXXXXX")
chmod 700 "$work"
bundle_id=com.jql.duoduoxue
seed="$PWD/courses/dist/dlg_q.db"
```

使用 `xcrun devicectl ... --json-output <file>` 获取机器可读结果，不解析表格文本：

```bash
xcrun devicectl list devices --timeout 15 --json-output "$work/devices.json"
```

只选择 `hardwareProperties.reality=physical`、`deviceType=iPhone` 且 tunnel 可用的唯一设备。然后用以下命令查询 App 数量：

```bash
xcrun devicectl device info apps \
  --device "$device" --bundle-id "$bundle_id" \
  --json-output "$work/apps.json"
```

设备不可用时停止。App 查询结果为零时只走“全新安装”分支；恰好一个但已确认 provisioning/签名失效时只走“覆盖续签”分支；正常已安装时继续第 2 节，并按数据库是否存在分流。结果多于一个或状态无法判定时停止。

## 2. 静止数据库

只解析 JSON，按 `$work/apps.json` 中该 App 的可执行文件信息识别其进程，不用表格文本或模糊进程名。查询、逐一终止匹配 PID、再查询的完整命令为：

```bash
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-before.json"

xcrun devicectl device process terminate \
  --device "$device" --pid "$pid" \
  --json-output "$work/terminate-$pid.json"

xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-after-terminate.json"
```

`terminate` 对每个匹配 PID 执行一次。每条命令都必须成功，且最后一个 JSON 中该 App 的匹配进程数必须为 0；否则保留 `$work` 并停止。

列出容器 `Documents`：

```bash
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$work/files-before.json"
```

若 `dlg_q.db-wal`、`dlg_q.db-shm` 或 `dlg_q.db-journal` 任一存在，停止，不复制单独的主库。无 sidecar 时只按 `files-before.json` 作以下分流：

- `Documents/dlg_q.db` 存在：先在第 3 节拉取并完整校验；有效库走增量。无效库只有在保留证据能证明它来自失败的首次注入时，才进入对应失败分类；不得自动 seed 覆盖。
- `Documents/dlg_q.db` 不存在：App 已安装但未初始化，跳到“首次注入共用本地校验”，不得进入第 3 节。

## 3. 拉取与合并

```bash
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/device.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/pull.json"
cp -p "$work/device.db" "$work/device.backup.db"
shasum -a 256 "$work/device.backup.db" >"$work/device.backup.sha256"
cp -p "$seed" "$work/seed-merge.db"
chmod 600 "$work/seed-merge.db"
shasum -a 256 "$work/seed-merge.db" >"$work/seed-merge.sha256"

python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$work/device.db" --seed-db "$work/seed-merge.db" \
  --output "$work/merged.db" \
  >"$work/merge-result.json" 2>"$work/merge-error.json"
```

检查 JSON 结果。若包含非空 `warnings`，保留其中给出的 0700 staging 路径并停止，不得调用 `copy to`。无 warning 且 `added_decks=0`、`added_questions=0` 时也不得调用 `copy to`。

若合并器因设备库损坏、schema 或 integrity 错误而失败，不得写设备。若用户提供上次首次注入保留的 `$work`，且其中有 `files-before-seed.json`、`processes-before-seed.json`、`seed-attempt.db` 和 `seed-attempt.sha256`，进入“首次注入失败分类”；否则保留当前 `$work` 和 `merge-error.json`，报告需要人工判定。不可变内容冲突不等于数据库损坏；遇到这种错误时保留设备库并停止，不得进入 seed 替换。

## 4. 写回与回读

仅在存在新增时执行。以下门禁必须紧邻首次 `copy to`，中间不得启动 App 或执行无关操作。

先重新查询进程：

```bash
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-prewrite.json"
```

若发现该 App 曾重新启动，逐一执行：

```bash
xcrun devicectl device process terminate \
  --device "$device" --pid "$pid" \
  --json-output "$work/terminate-prewrite-$pid.json"
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-prewrite-after-terminate.json"
```

确认最后一个 JSON 中匹配进程数为 0 后，当前 `merged.db` 仍视为已失效：禁止写回，保留并报告 `$work`，结束本次执行。下一次必须创建新的 `$work`，从第 1 节重新选择设备并查询 App，再完整执行第 2 节的进程与 sidecar 门禁；只有门禁重新成立后才可进入第 3 节。不得从第 3 节直接续跑，也不得复用旧候选。

若没有匹配进程，重新检查 sidecar，再拉取写前快照：

```bash
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$work/files-prewrite.json"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/prewrite.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/prewrite.json"
cmp "$work/device.db" "$work/prewrite.db"
```

`files-prewrite.json` 中任一 `dlg_q.db-wal`、`dlg_q.db-shm`、`dlg_q.db-journal` 都会使候选失效。`copy from` 或 `cmp` 失败也表示最初快照不新鲜。以上任一情况均禁止写回，保留并报告 `$work` 后停止。

只有门禁全部成功才立即写回并回读。从下面第一条 `copy to` 命令本身开始，任一命令非零、JSON 报错、`cmp` 不同、回读合并结果不是 0/0、出现 warning，或最终存在 sidecar，都立即进入第 5 节；不得把 `copy to` 失败解释为设备库未变化，也不得继续执行普通成功路径。

```bash
xcrun devicectl device copy to \
  --device "$device" --source "$work/merged.db" \
  --destination Documents/dlg_q.db \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/write.json"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/readback.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/readback.json"
cmp "$work/merged.db" "$work/readback.db"
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$work/readback.db" --seed-db "$work/seed-merge.db" \
  --output "$work/readback-check.db" \
  >"$work/readback-check.json" 2>"$work/readback-check-error.json"
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$work/files-after.json"
```

`files-after.json` 必须无 sidecar，回读合并结果必须为 0/0。

## 5. 增量写后失败分类

第 4 节从首次 `copy to` 本身开始的任一失败都进入本节。每次进入（包括停止后重入）都先分配新的分类目录；不得复用旧目录或覆盖旧证据。`backup-stale` 是 sticky 目录，事件文件由 `mktemp` 唯一命名并改为只读：

```bash
failure_attempt=$(mktemp -d "$work/failure-attempt.XXXXXX")
chmod 700 "$failure_attempt"
mark_backup_stale() {
  reason=$1
  marker_dir="$work/backup-stale"
  if ! test -d "$marker_dir"; then
    mkdir -m 700 "$marker_dir" || exit 1
  fi
  event=$(mktemp "$marker_dir/event.XXXXXX") || exit 1
  printf '%s\n' "$reason" >"$event" || exit 1
  chmod 400 "$event"
}
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$failure_attempt/processes-before.json"
```

只解析 `processes-before.json`。若观察到任一匹配进程，必须在终止进程或执行其他设备命令前先执行 `mark_backup_stale "process observed: $failure_attempt/processes-before.json"`，再对每个匹配 PID 执行：

```bash
mark_backup_stale "process observed: $failure_attempt/processes-before.json"
xcrun devicectl device process terminate \
  --device "$device" --pid "$pid" \
  --json-output "$failure_attempt/terminate-$pid.json"
```

随后确认进程并列出文件：

```bash
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$failure_attempt/processes-confirm.json"
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$failure_attempt/files-before.json"
```

`terminate` 对首个查询中的每个匹配 PID 执行一次。只要首个 JSON 观察到 App 进程，旧 backup 就永久不新鲜，即使随后成功终止也不删除 marker。命令失败或确认后匹配进程不为 0 时，保留现场并停止；再次进入本节必须创建另一个 `failure-attempt.*`。

`files-before.json` 中出现任一 sidecar 时，必须立即执行 `mark_backup_stale "sidecar observed: $failure_attempt/files-before.json"`，再停止；不得复制单独主库、删除 sidecar 或写设备。重入不得覆盖这次 attempt 或既有 event。

文件存在性只用以下三态解析器判断。它只接受 JSON v3 的成功 `devicectl.device.info.files` envelope，以及 `result.files` 中全部带字符串 `relativePath` 的对象记录；完整枚举后才输出 `present` 或 `absent`。其他结构一律输出 `unknown` 并返回非零：

```bash
canonical_presence() {
  python3 - "$1" <<'PY'
import json
import sys
from pathlib import PurePosixPath

def unknown():
    print("unknown")
    raise SystemExit(1)

try:
    with open(sys.argv[1], encoding="utf-8") as source:
        envelope = json.load(source)
except (OSError, UnicodeError, json.JSONDecodeError):
    unknown()

if not isinstance(envelope, dict) or set(envelope) != {"info", "result"}:
    unknown()

info = envelope["info"]
result = envelope["result"]
if (
    not isinstance(info, dict)
    or info.get("jsonVersion") != 3
    or info.get("outcome") != "success"
    or info.get("commandType") != "devicectl.device.info.files"
    or not isinstance(result, dict)
    or not isinstance(result.get("files"), list)
):
    unknown()

paths = []
for record in result["files"]:
    if not isinstance(record, dict):
        unknown()
    relative_path = record.get("relativePath")
    if not isinstance(relative_path, str):
        unknown()
    paths.append(relative_path)

print(
    "present"
    if any(PurePosixPath(path).name == "dlg_q.db" for path in paths)
    else "absent"
)
PY
}

canonical_presence_expect_unknown() {
  local output
  if output=$(canonical_presence <(printf '%s\n' "$1") 2>/dev/null); then
    return 1
  fi
  test "$output" = unknown
}

canonical_presence_self_check() {
  test "$(canonical_presence <(printf '%s\n' '{"info":{"jsonVersion":3,"outcome":"success","commandType":"devicectl.device.info.files"},"result":{"files":[{"relativePath":"Documents/dlg_q.db"}]}}'))" = present || return 1
  test "$(canonical_presence <(printf '%s\n' '{"info":{"jsonVersion":3,"outcome":"success","commandType":"devicectl.device.info.files"},"result":{"files":[]}}'))" = absent || return 1
  canonical_presence_expect_unknown '{' || return 1
  canonical_presence_expect_unknown '{"info":{"jsonVersion":3,"outcome":"failed","commandType":"devicectl.device.info.files"},"result":{"files":[]}}' || return 1
  canonical_presence_expect_unknown '{"info":{"jsonVersion":3,"outcome":"success","commandType":"devicectl.device.info.files"},"result":{"items":[]}}' || return 1
  canonical_presence_expect_unknown '{"info":{"jsonVersion":3,"outcome":"success","commandType":"devicectl.device.info.files"},"result":{"files":[{"relativePath":"Documents/dlg_q.db"},null]}}'
}
canonical_presence_self_check || exit 1
```

确认进程为 0 且无 sidecar 后，只解析文件 JSON。`unknown` 必须在分类前停止；`present` 时拉取并只在本地分类，与 backup 不同必须在继续校验前写 sticky event。`absent` 表示写后现场已变化，同样先写 event 并停止在“当前库不存在”的人工分类，不执行必失败的拉取：

```bash
failure_present=$(canonical_presence "$failure_attempt/files-before.json") || {
  printf '%s\n' "$failure_present" >&2
  exit 1
}
if test "$failure_present" = present; then
  xcrun devicectl device copy from \
    --device "$device" --source Documents/dlg_q.db \
    --destination "$failure_attempt/current.db" \
    --domain-type appDataContainer --domain-identifier "$bundle_id" \
    --json-output "$failure_attempt/current-pull.json"
  if cmp "$failure_attempt/current.db" "$work/merged.db"; then
    current_is_merged=1
  else
    current_is_merged=0
  fi
  if cmp "$failure_attempt/current.db" "$work/device.backup.db"; then
    current_is_backup=1
  else
    current_is_backup=0
    mark_backup_stale "canonical differs from backup: $failure_attempt/current.db"
  fi
  python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
    --device-db "$failure_attempt/current.db" \
    --seed-db "$work/seed-merge.db" \
    --output "$failure_attempt/current-check.db" \
    >"$failure_attempt/current-check.json" \
    2>"$failure_attempt/current-check-error.json"
elif test "$failure_present" = absent; then
  mark_backup_stale "canonical absent: $failure_attempt/files-before.json"
  current_is_merged=0
  current_is_backup=0
else
  printf '无效的 canonical presence 状态\n' >&2
  exit 1
fi
```

两个 `if` 是独立分类探针，`cmp` 返回不同不算流程错误。合并器在本地检查 schema v1、integrity、外键和内容冲突。结果含 warning 也不算通过；若错误 JSON 明确表示在结构与完整性检查之后发现不可变内容冲突，当前库仍属于有效但不兼容的库，必须保留，绝不能当作损坏库覆盖。按以下顺序分类，分类本身不写设备：

1. `current.db` 与 `merged.db` 字节一致，且完整校验成功、结果为 0/0：设备已是预期合并库。保留当前库，不恢复 backup；用该拉取副本完成 `cmp`、0/0 和无 sidecar 后置检查后可进入第 6 节。
2. `current.db` 与 `device.backup.db` 字节一致，且 `shasum -a 256 -c "$work/device.backup.sha256"` 成功：首次写入未改变设备。无需恢复；保留 `$work`，新建工作目录并从第 1 节重试。
3. 与两者都不同，但完整校验成功，或错误 JSON 明确表示结构与完整性检查通过后发生不可变内容冲突：当前库可能含写后学习进度。旧 backup 立即判为不新鲜；保留设备当前库，不复制本地检查产物。保留并报告旧 `$work`，再用新 `$work` 从第 1 节开始，以设备当前库为基底重做增量或报告内容冲突。
4. 当前库不存在、无法拉取，或因 header、schema、integrity、外键等结构性错误而无法完整校验：保留设备现场、整个 `$failure_attempt`、backup 和 merged；不启动、不写设备。报告这些绝对路径和下面的人工恢复入口。

任何观察到的 App 进程、sidecar、canonical 缺失或 `current.db` 与 backup 不同，都必须已经产生独立的只读 `backup-stale/event.*`。marker 不随重入清除；旧 backup 始终禁止自动写回。

### 经明确授权的旧备份恢复

普通部署请求不构成恢复授权。只有用户在看到上述分类证据后再次明确指定 `$failure_attempt` 与 `$work/device.backup.db`，确认 App 自该快照后没有需要保留的进度，并授权覆盖当前库，才可进入。每次进入先创建唯一恢复目录。只要 sticky marker 存在，默认拒绝该授权：列出全部 event 后立即停止，不得执行本节后续命令。

```bash
restore_attempt=$(mktemp -d "$work/restore-attempt.XXXXXX")
chmod 700 "$restore_attempt"
mark_backup_stale() {
  reason=$1
  marker_dir="$work/backup-stale"
  if ! test -d "$marker_dir"; then
    mkdir -m 700 "$marker_dir" || exit 1
  fi
  event=$(mktemp "$marker_dir/event.XXXXXX") || exit 1
  printf '%s\n' "$reason" >"$event" || exit 1
  chmod 400 "$event"
}
if test -d "$work/backup-stale"; then
  find "$work/backup-stale" -type f -name 'event.*' -print \
    >"$restore_attempt/pending-stale-markers.txt"
  chmod 400 "$restore_attempt/pending-stale-markers.txt"
  printf 'backup-stale marker 存在；必须逐项重新授权\n' >&2
  exit 1
fi
```

若上一步因 marker 停止，必须把 `pending-stale-markers.txt` 和每个 event 的内容展示给用户。只有用户随后再次明确点名并承认每个 event 所代表的进程、sidecar 或新鲜度变化，同时再次确认允许丢失其后的全部进度，才可重新进入。重新进入仍创建新的 `restore-attempt.*`，并把当时全部 marker 的哈希写成只读授权回执；不得删除、改名或覆盖 marker：

```bash
restore_attempt=$(mktemp -d "$work/restore-attempt.XXXXXX")
chmod 700 "$restore_attempt"
find "$work/backup-stale" -type f -name 'event.*' \
  -exec shasum -a 256 {} \; \
  >"$restore_attempt/acknowledged-stale-markers.sha256"
test -s "$restore_attempt/acknowledged-stale-markers.sha256"
chmod 400 "$restore_attempt/acknowledged-stale-markers.sha256"
mark_backup_stale() {
  reason=$1
  event=$(mktemp "$work/backup-stale/event.XXXXXX") || exit 1
  printf '%s\n' "$reason" >"$event" || exit 1
  chmod 400 "$event"
}
```

无 marker 时使用第一次创建的恢复目录；有 marker 且已取得上述逐项新授权时使用带哈希回执的新目录。先验证 backup 哈希和完整性，再查询进程。若查询观察到匹配进程，必须先创建新的 sticky event，再终止进程、停止并重新分类；本次授权不得继续使用。

```bash
shasum -a 256 -c "$work/device.backup.sha256"
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$work/device.backup.db" \
  --seed-db "$work/seed-merge.db" \
  --output "$restore_attempt/backup-check.db" \
  >"$restore_attempt/backup-check.json" \
  2>"$restore_attempt/backup-check-error.json"
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$restore_attempt/processes.json"
```

只解析 `processes.json`。发现匹配进程时，在任何其他设备操作前执行 `mark_backup_stale "process observed during restore: $restore_attempt/processes.json"`；可逐个终止，但随后必须停止并用新 `failure-attempt.*` 重新分类。没有匹配进程时才继续二次确认和文件查询：

```bash
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$restore_attempt/processes-confirm.json"
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$restore_attempt/files.json"
```

backup 校验必须成功且无 warning，确认进程数必须为 0。`files.json` 出现 sidecar 时，立即执行 `mark_backup_stale "sidecar observed during restore: $restore_attempt/files.json"` 并停止。无 sidecar 后，复用上面的 `canonical_presence` 重新解析分类与授权时的两份文件列表；任一 `unknown` 都必须先停止：

```bash
failure_present=$(canonical_presence "$failure_attempt/files-before.json") || {
  printf '%s\n' "$failure_present" >&2
  exit 1
}
authorized_present=$(canonical_presence "$restore_attempt/files.json") || {
  printf '%s\n' "$authorized_present" >&2
  exit 1
}
if test "$failure_present" = present && test "$authorized_present" = present; then
  if ! xcrun devicectl device copy from \
    --device "$device" --source Documents/dlg_q.db \
    --destination "$restore_attempt/current.db" \
    --domain-type appDataContainer --domain-identifier "$bundle_id" \
    --json-output "$restore_attempt/current-pull.json"; then
    exit 1
  fi
  if ! cmp "$failure_attempt/current.db" "$restore_attempt/current.db"; then
    mark_backup_stale "canonical changed during restore: $restore_attempt/current.db"
    exit 1
  fi
elif test "$failure_present" = absent && test "$authorized_present" = absent; then
  :
else
  mark_backup_stale "canonical presence changed: $failure_attempt $restore_attempt"
  exit 1
fi
```

只有两次都 `present` 才执行 `copy from` 与 `cmp`；两次都 `absent` 才跳过。JSON malformed、envelope 或 list schema 未知、记录不是对象、缺少字符串 `relativePath` 时均为 `unknown`，必须在比较状态前停止；两个已确认状态不同则立即写 marker 并停止。DB present 却无法拉取、`cmp` 不同或其他命令失败都会使授权失效，必须保留证据并用新 attempt 重新分类；不得写设备。

只有授权与上述条件全部仍有效时才可人工恢复，并立即回读：

```bash
xcrun devicectl device copy to \
  --device "$device" --source "$work/device.backup.db" \
  --destination Documents/dlg_q.db \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$restore_attempt/write.json"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$restore_attempt/readback.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$restore_attempt/readback.json"
cmp "$work/device.backup.db" "$restore_attempt/readback.db"
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$restore_attempt/readback.db" \
  --seed-db "$work/seed-merge.db" \
  --output "$restore_attempt/readback-check.db" \
  >"$restore_attempt/readback-check.json" \
  2>"$restore_attempt/readback-check-error.json"
```

任一恢复或回读检查失败都用新的 `failure-attempt.*` 返回分类，不得再次自动覆盖。即使人工恢复成功，本次同步仍按失败处理，保留 `$work`，不启动 App；后续增量使用新 `$work` 从第 1 节开始。

## 6. 启动与清理

增量写回及全部回读检查成功、确认 no-op，或首次注入回读成功时才可启动。launch 与清理必须用 shell 控制流绑定；launch 失败时保留并报告证据目录，清理失败时报告可能残留的绝对路径：

```bash
if xcrun devicectl device process launch \
  --device "$device" --terminate-existing \
  --json-output "$work/launch.json" "$bundle_id"; then
  if ! rm -rf -- "$work"; then
    printf '清理失败，检查残留目录: %s\n' "$work" >&2
    exit 1
  fi
else
  printf '启动失败，证据保留于: %s\n' "$work" >&2
  exit 1
fi
```

## Release 例外

只有 App 缺失或已确认 provisioning/签名失效时才构建并安装。把产物绝对路径记为 `app_path`。两种情况都只接受以 `Release` configuration 构建且通过 `codesign --verify --deep --strict "$app_path"` 的签名 `Runner.app`；拒绝 `Debug-iphoneos` 路径、Debug 产物和 `flutter run`。已安装但未初始化不属于重装条件。

先尝试当前工程的签名 Release。若 Personal Team 拒绝 App Group：

1. 用 `ditto` 创建临时仓库副本。
2. 只在临时副本移除 Share Extension 的 target、嵌入关系与 App Group entitlements。
3. 在临时副本构建、签名并检查产物确为 Release。
4. 用 `git status --short` 确认原仓库没有因签名降级产生改动。

临时副本规则对下面两个分支相同，原仓库必须保持不变。

### 首次注入共用本地校验

全新安装和已安装但未初始化都必须执行此块。全新安装必须在 `install app` 之前执行；已安装但未初始化必须在“首次注入写入门禁”之前执行。校验失败时保留并报告 `$work`，不安装、不写设备：

```bash
python3 courses/build.py --check
test -s "$seed"
test "$(sqlite3 "$seed" 'PRAGMA quick_check;')" = ok
test -z "$(sqlite3 "$seed" 'PRAGMA foreign_key_check;')"
cp -p "$seed" "$work/seed-attempt.db"
chmod 600 "$work/seed-attempt.db"
cmp "$seed" "$work/seed-attempt.db"
shasum -a 256 "$work/seed-attempt.db" >"$work/seed-attempt.sha256"
```

### 全新安装

仅当 `apps.json` 证明 `$bundle_id` 未安装时使用。先完成共用本地校验，再构建、签名、检查 Release，最后安装；安装后不得启动，直接进入“首次注入写入门禁”：

```bash
xcrun devicectl device install app \
  --device "$device" \
  --json-output "$work/install-new.json" "$app_path"
```

安装失败时保留并报告 `$work`，不得启动或卸载 App。

### 已安装但未初始化

第 2 节确认 App 恰好安装一次、无匹配进程、`Documents/dlg_q.db` 不存在且无三种 sidecar 时进入。不要重装；完成共用本地校验后进入“首次注入写入门禁”。上一次安装、查询或校验失败后可重新进入；`copy to` 或回读失败后也必须从第 1、2 节重新判定。数据库不存在时可重试首次注入；数据库存在时先分类，有效库切换到增量，无效或部分库进入“首次注入失败分类”。

### 首次注入写入门禁

本地校验完成且 App 已安装后，紧邻 seed `copy to` 依次重查 App、进程和 `Documents`；中间不得执行本地构建、SQLite 检查、启动 App 或其他无关操作：

```bash
xcrun devicectl device info apps \
  --device "$device" --bundle-id "$bundle_id" \
  --json-output "$work/apps-before-seed.json"
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-before-seed.json"
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$work/files-before-seed.json"
```

只解析 JSON。`apps-before-seed.json` 必须恰好包含一个 App；`processes-before-seed.json` 中该 App 的匹配进程数必须为 0；`files-before-seed.json` 必须同时不存在 `dlg_q.db` 和三种 sidecar。三项条件全部保持时，把这三个 JSON、`seed-attempt.db` 和 `seed-attempt.sha256` 作为“目标原先不存在及写入字节”的 0700 `$work` 证据，不得覆盖这些文件名；然后立即复制冻结的 seed 并回读：

```bash
xcrun devicectl device copy to \
  --device "$device" --source "$work/seed-attempt.db" \
  --destination Documents/dlg_q.db \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/seed-write.json"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/seed-readback.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/seed-readback.json"
cmp "$work/seed-attempt.db" "$work/seed-readback.db"
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$work/seed-readback.db" \
  --seed-db "$work/seed-attempt.db" \
  --output "$work/seed-readback-check.db" \
  >"$work/seed-readback-check.json" \
  2>"$work/seed-readback-check-error.json"
```

若门禁时出现匹配进程或任一 sidecar，禁止 seed 覆盖，保留并报告 `$work` 后停止；下一次从第 1 节重新判定。若 `dlg_q.db` 已存在，即使进程数为 0 也禁止 seed 覆盖，返回第 2 节重新建立静止门禁后走设备库增量流程。App 数量异常或门禁查询失败时同样停止。

从 seed `copy to` 命令本身开始，写入、回读、`cmp` 或完整校验任一失败，或校验结果不是无 warning 的 0/0，都必须进入“首次注入失败分类”；不得假定失败的 `copy to` 没有创建或截断 canonical DB。只有全部成功后才可按第 6 节启动与清理。

### 首次注入失败分类

本节既处理刚发生的首次注入失败，也处理下一次执行时第 3 节因损坏 DB 失败、且用户提供了保留证据 `$work` 的情况。不得启动 App。先重新静止并检查 sidecar：

```bash
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-seed-failure-before.json"
xcrun devicectl device process terminate \
  --device "$device" --pid "$pid" \
  --json-output "$work/terminate-seed-failure-$pid.json"
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-seed-failure-confirm.json"
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$work/files-seed-failure.json"
```

`terminate` 对首个查询中的每个匹配 PID 执行一次。任何命令失败、确认后进程数不为 0，或文件列表含 sidecar 时，保留现场并停止；不得复制单独主库、删除 sidecar 或写设备。

若 `files-seed-failure.json` 证明 `dlg_q.db` 不存在，设备仍是未初始化状态。保留旧 `$work` 作为失败证据，使用新 `$work` 从第 1 节重试。若数据库存在，拉取并验证冻结 seed 哈希，再仅在本地完整校验当前库：

```bash
shasum -a 256 -c "$work/seed-attempt.sha256"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/current-seed-failure.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/current-seed-failure-pull.json"
if cmp "$work/current-seed-failure.db" "$work/seed-attempt.db"; then
  current_is_seed=1
else
  current_is_seed=0
fi
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$work/current-seed-failure.db" \
  --seed-db "$work/seed-attempt.db" \
  --output "$work/current-seed-failure-check.db" \
  >"$work/current-seed-failure-check.json" \
  2>"$work/current-seed-failure-check-error.json"
```

这个 `if` 是分类探针，`cmp` 返回不同不算流程错误。按以下顺序分类，任何分类都先保留 `$work`：

1. 当前库与 `seed-attempt.db` 字节一致，且完整校验成功、无 warning、结果 0/0：认定首次写入成功。当前拉取副本就是回读证据，可进入第 6 节。
2. 当前库与 seed 不同，但完整校验成功，或错误 JSON 明确表示结构与完整性检查通过后发生不可变内容冲突：它是有效 schema v1，可能含用户数据。禁止 seed 覆盖；保留设备当前库，用新 `$work` 从第 1 节开始，以它为基底走增量或报告内容冲突。
3. 当前库无法拉取，或因 header、schema、integrity、外键等结构性错误而无法完整校验：视为无效或部分库。不得自动覆盖；保留设备现场、目标原先不存在的 JSON、seed 哈希、当前拉取副本和错误 JSON，报告下面的人工恢复入口。

### 经明确授权的首次注入恢复

普通部署请求不构成恢复授权。只有同时满足以下条件，才可替换已经存在的无效库：

1. 保留的 `files-before-seed.json` 证明写前 `dlg_q.db` 与三种 sidecar 均不存在，`processes-before-seed.json` 证明匹配进程数为 0。
2. `shasum -a 256 -c "$work/seed-attempt.sha256"` 成功，且当前库已按上一节判为无效或部分库；有效库绝不进入此分支。
3. 用户在看到当前库、错误 JSON 和 seed 哈希后，再次明确确认该 App 没有任何需要保留的进度，并授权用这个 `seed-attempt.db` 替换。先前的一般部署授权无效。

取得授权后仍须重新静止、重查 sidecar 并确认现场未变化：

```bash
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-authorized-seed-recovery.json"
xcrun devicectl device process terminate \
  --device "$device" --pid "$pid" \
  --json-output "$work/terminate-authorized-seed-recovery-$pid.json"
xcrun devicectl device info processes \
  --device "$device" \
  --json-output "$work/processes-authorized-seed-recovery-confirm.json"
xcrun devicectl device info files \
  --device "$device" --domain-type appDataContainer \
  --domain-identifier "$bundle_id" --subdirectory Documents \
  --no-recurse --json-output "$work/files-authorized-seed-recovery.json"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/current-before-authorized-seed-recovery.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/current-before-authorized-seed-recovery.json"
cmp "$work/current-seed-failure.db" \
  "$work/current-before-authorized-seed-recovery.db"
```

确认后进程数必须为 0、文件列表必须无 sidecar，最新当前库必须与已分类的无效库字节一致；任一条件失败都会使授权依据失效，必须停止并重新分类。条件仍成立时才可人工替换并回读：

```bash
xcrun devicectl device copy to \
  --device "$device" --source "$work/seed-attempt.db" \
  --destination Documents/dlg_q.db \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/authorized-seed-recovery-write.json"
xcrun devicectl device copy from \
  --device "$device" --source Documents/dlg_q.db \
  --destination "$work/authorized-seed-recovery-readback.db" \
  --domain-type appDataContainer --domain-identifier "$bundle_id" \
  --json-output "$work/authorized-seed-recovery-readback.json"
cmp "$work/seed-attempt.db" \
  "$work/authorized-seed-recovery-readback.db"
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$work/authorized-seed-recovery-readback.db" \
  --seed-db "$work/seed-attempt.db" \
  --output "$work/authorized-seed-recovery-check.db" \
  >"$work/authorized-seed-recovery-check.json" \
  2>"$work/authorized-seed-recovery-check-error.json"
```

恢复回读必须完整校验成功、无 warning、结果 0/0。任一写入或检查失败都返回“首次注入失败分类”，不得自动再次覆盖。成功后才可按第 6 节启动与清理；这是“数据库存在时禁止 seed 覆盖”的唯一例外。

### 签名失效续签

仅当 App 已安装且已确认 provisioning/签名失效时使用。先按第 2 节终止并确认进程消失；确认 Release 的 `CFBundleIdentifier` 精确等于 `$bundle_id` 后，使用相同 bundle id 覆盖安装：

```bash
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' \
  "$app_path/Info.plist")" = "$bundle_id"
xcrun devicectl device install app \
  --device "$device" \
  --json-output "$work/install-renewal.json" "$app_path"
```

绝不调用卸载，也不直接注入种子库。覆盖安装成功后不得启动 App；重新执行第 1 节的 App 查询，再返回第 2 节。若数据库存在，走设备库增量；若数据库不存在且无进程、无 sidecar，走“已安装但未初始化”首次注入。首次开发者信任仍由用户在 iPhone 设置中完成。
