# 我的 Codex Harness：Mac 实验手册

本手册对应 Codex CLI `0.144.6` 与 `$HOME/.codex` 的 `2026-07-20` 脱敏快照，并以 OpenAI 官方 Customization 文档校准术语。默认实验全部只读：只显示版本、帮助、键名、功能状态、安装状态、布尔存在性或已脱敏路径；不读取凭证或运行态材料，不输出任何 secret。

## 操作边界

- 先运行每节的“只读验证”，再决定是否需要持续改造。
- 本手册不要求持久写入，也不安排删除型练习。
- 不复制完整配置，不展开环境变量、请求头或认证值。
- 命令输出若含主目录，先替换为字面量 `$HOME` 再记录。
- “文件存在”“配置登记”“已安装”“当前任务可用”“模型可见”“实际使用”始终分别取证。

如自行做持续改造，所有写入统一使用下面的备份、验证、复制回滚协议。每次只改一个现有文件；`TARGET` 必须先指向已确认的非凭证配置或指导文件。本手册各节不要求执行这段协议。

```sh
TARGET="$HOME/.codex/config.toml"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${TARGET}.before-${STAMP}"

# 备份
cp -p "$TARGET" "$BACKUP"

# 此处只修改一个已审查的非秘密设置，然后验证。
# mcp-server 是支持 strict-config 的运行时命令，stdin EOF 后直接退出。
codex --strict-config mcp-server </dev/null >/dev/null

# 需要回滚时复制原文件回来，再验证
cp -p "$BACKUP" "$TARGET"
codex --strict-config mcp-server </dev/null >/dev/null
```

## CX01 凭证安全

### 目标

建立允许读取的最小清单，确认版本和非秘密权限基线，避免“先读取、后脱敏”。

### 只读验证

```sh
codex --version

awk '
  BEGIN { in_table=0 }
  /^[[:space:]]*\[/ { in_table=1 }
  in_table { next }
  /^[[:space:]]*approval_policy[[:space:]]*=[[:space:]]*"untrusted"[[:space:]]*(#.*)?$/ {
    print "approval_policy=untrusted"
  }
  /^[[:space:]]*approval_policy[[:space:]]*=[[:space:]]*"on-request"[[:space:]]*(#.*)?$/ {
    print "approval_policy=on-request"
  }
  /^[[:space:]]*approval_policy[[:space:]]*=[[:space:]]*"never"[[:space:]]*(#.*)?$/ {
    print "approval_policy=never"
  }
  /^[[:space:]]*sandbox_mode[[:space:]]*=[[:space:]]*"read-only"[[:space:]]*(#.*)?$/ {
    print "sandbox_mode=read-only"
  }
  /^[[:space:]]*sandbox_mode[[:space:]]*=[[:space:]]*"workspace-write"[[:space:]]*(#.*)?$/ {
    print "sandbox_mode=workspace-write"
  }
  /^[[:space:]]*sandbox_mode[[:space:]]*=[[:space:]]*"danger-full-access"[[:space:]]*(#.*)?$/ {
    print "sandbox_mode=danger-full-access"
  }
' "$HOME/.codex/config.toml"

codex --help | sed -n '/--sandbox/,/--search/p'
```

### 观察要点

- 版本应为 `codex-cli 0.144.6`。
- 提取器只检查首个 TOML 表之前的顶层键，只打印已知枚举的固定字面量；嵌套同名键、未知值与行尾注释都不会进入输出。
- 脱敏快照的非秘密策略值为 `sandbox_mode="danger-full-access"` 与 `approval_policy="never"`。
- Full Access 与 Never 都是运行边界，不是“更聪明”或“更安全”的模式；组合后不会依赖人工确认兜底。
- 不要为了确认认证是否存在而打开任何凭证文件，也不要显示环境变量值。

### 通过标准

终端只出现版本、两个白名单策略值和帮助文本，没有配置其他字段、认证材料或个人绝对路径。

## CX02 有效配置

### 目标

区分“文件里写了键”“当前版本接受该键”和“当前任务采用该值”。

### 只读验证

```sh
codex features list | sed -n '1,40p'

STRICT_ERR="$(mktemp "${TMPDIR:-/tmp}/codex-strict.XXXXXX")"
trap 'rm -f "$STRICT_ERR"' EXIT HUP INT TERM
if codex --strict-config mcp-server </dev/null >/dev/null 2>"$STRICT_ERR"; then
  printf 'strict_config=accepted\n'
else
  printf 'strict_config=rejected\n'
  python3 -c 'import os, sys; print(sys.stdin.read().replace(os.path.expanduser("~"), "$HOME"), end="")' \
    <"$STRICT_ERR" | sed -n '1,8p'
fi
rm -f "$STRICT_ERR"
trap - EXIT HUP INT TERM

sed -n -E \
  -e 's/^[[:space:]]*(approval_policy|sandbox_mode|personality|model_reasoning_effort)[[:space:]]*=.*$/key:\1/p' \
  -e 's/^\[(plugins|mcp_servers|hooks|features|memories)(\..*)?\]$/table:\1/p' \
  "$HOME/.codex/config.toml" | sort -u
```

### 观察要点

- `codex features list` 只观察功能清单；0.144.6 的 `features` 子命令不支持 `--strict-config`。
- `mcp-server` 是支持 `--strict-config` 的运行时命令；标准输入立即 EOF，因此解析后退出，不发起模型请求。
- 第二条命令只显示白名单键名和表类别，不显示右侧值。
- strict-config 成功只证明语法与字段被接受；该键是否允许出现在当前层、是否受 `requirements.toml` 限制，以及外部服务能否启动仍需单独证据。

### 通过标准

功能列表正常返回，结构输出只包含 `key:` 或 `table:` 行；若严格解析失败，只记录已将主目录替换为 `$HOME` 的错误和版本，不改动原文件。

## CX03 AGENTS作用域

### 目标

验证全局 override/base 的候选顺序与幽灵路径，但不把“存在”误判为“加载”。

### 只读验证

```sh
test -f "$HOME/.codex/AGENTS.override.md" \
  && printf 'global_agents_override=yes\n' \
  || printf 'global_agents_override=no\n'

test -f "$HOME/.codex/AGENTS.md" \
  && printf 'global_agents_base=yes\n' \
  || printf 'global_agents_base=no\n'

test -f "$HOME/.codex/.codex/AGENTS.md" \
  && printf 'ghost_agents=yes\n' \
  || printf 'ghost_agents=no\n'

printf '%s\n' "$PWD" "$(git rev-parse --show-toplevel 2>/dev/null || printf 'no-git-root')" \
  | python3 -c 'import os, sys; print(sys.stdin.read().replace(os.path.expanduser("~"), "$HOME"), end="")'
```

### 观察要点

- 全局层先查 `$HOME/.codex/AGENTS.override.md`，不存在时才回退到 `$HOME/.codex/AGENTS.md`；同一层不会把两份正文合并。
- `$HOME/.codex/.codex/AGENTS.md` 在快照中存在，但多一层目录；这只是磁盘证据，不自动成为全局指导。
- 项目指导从项目根走到当前目录，靠近当前目录的文件后生效；指令链在新启动时重建。
- 需要确认加载性时，在目标目录开启新任务，只询问已加载来源类别，不要求回显正文。

### 通过标准

得到三个 yes/no 和脱敏后的工作目录信息；没有读取任一 AGENTS 正文，也没有移动或改写文件。

## CX04 配置分层

### 目标

按正确优先级定位配置来源，并确认项目层是否有资格加载。

### 只读验证

```sh
codex --help | sed -n '/--config/,/--image/p'

test -f "$HOME/.codex/config.toml" \
  && printf 'user_config=yes\n' \
  || printf 'user_config=no\n'

python3 - <<'PY'
from pathlib import Path
import subprocess

cwd = Path.cwd().resolve()
try:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = Path(result.stdout.strip()).resolve()
    relative = cwd.relative_to(root)
except (OSError, subprocess.CalledProcessError, ValueError):
    root = cwd
    relative = cwd.relative_to(root)

directories = [root]
current = root
for part in relative.parts:
    current /= part
    directories.append(current)

for index, directory in enumerate(directories):
    present = "yes" if (directory / ".codex" / "config.toml").is_file() else "no"
    print(f"project_config[{index}]={present}")
PY

codex --strict-config mcp-server </dev/null >/dev/null 2>&1 \
  && printf 'strict_config=accepted\n' \
  || printf 'strict_config=rejected\n'
```

### 观察要点

配置优先级从高到低为：CLI 与 `--config`、受信任项目从根到当前目录的全部 `.codex/config.toml`、所选 Profile、用户配置、系统配置、内置默认值。项目链中越靠近当前目录的层越晚覆盖；未受信任项目会跳过项目本地配置、Hooks 与 Rules，但用户和系统层仍可加载。

### 通过标准

输出只说明帮助、根到当前目录各候选层的存在性和严格解析结果；没有显示路径或配置正文。能用优先级解释“用户文件值与当前任务值不同”的至少两个原因。

## CX05 Skill触发

### 目标

区分磁盘候选、当前任务可见元数据、模型选择与实际执行。

### 只读验证

```sh
python3 - <<'PY'
from pathlib import Path
import os
import subprocess

home = Path.home().resolve()
cwd = Path.cwd().resolve()
try:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    repo_root = Path(result.stdout.strip()).resolve()
    cwd.relative_to(repo_root)
except (OSError, subprocess.CalledProcessError, ValueError):
    repo_root = cwd

# 官方 REPO 来源按 CWD 到仓库根逐层扫描。
repo_roots = []
current = cwd
while True:
    repo_roots.append(("REPO", current / ".agents" / "skills"))
    if current == repo_root:
        break
    current = current.parent

roots = repo_roots + [
    ("USER", home / ".agents" / "skills"),
    ("ADMIN", Path("/etc/codex/skills")),
    ("LOCAL_EXTRA", home / ".codex" / "skills"),
]

shown = 0
for scope, root in roots:
    print(f"{scope}_root={'yes' if root.is_dir() else 'no'}")
    if not root.is_dir():
        continue
    try:
        candidates = sorted(root.rglob("SKILL.md"))
    except OSError:
        candidates = []
    for candidate in candidates:
        display = str(candidate).replace(str(home), "$HOME")
        print(f"{scope}_skill={display}")
        shown += 1
        if shown == 80:
            raise SystemExit
PY
```

再运行 `codex plugin list`，只观察 Plugin 的 STATUS 与已替换主目录的来源路径。最后在当前 Codex 任务使用 `/skills` 或 Skill 选择器，观察名称、描述、路径及 SYSTEM/Plugin 来源，不打开未选择 Skill 的正文。

### 观察要点

- 官方直接来源包括 CWD 到仓库根每层的 `.agents/skills`、`$HOME/.agents/skills`、`/etc/codex/skills` 与 Codex 内置 `SYSTEM`；本机 `$HOME/.codex/skills` 作为额外快照单列，不能替代官方来源分类。
- `SYSTEM` Skill 不要求可枚举的用户目录；Plugin 分发的 Skill 还要结合 `codex plugin list` 与当前任务元数据，不用缓存路径倒推安装状态。
- 路径枚举结果只是磁盘候选，不是安装、任务可用或触发证据。
- Codex 先向模型提供名称、描述和路径；选中后才读取完整 `SKILL.md`。
- 初始清单有上下文预算，候选很多时描述可能缩短或部分省略，因此磁盘候选与模型可见项可能不同。
- 关键流程应显式点名 Skill；隐式触发主要依赖 description。

### 通过标准

能按 REPO、USER、ADMIN、SYSTEM、Plugin 与本机额外来源解释候选差异，并列出磁盘候选、当前任务可见、是否有调用证据。没有执行候选 Skill 的脚本，也没有把目录存在写成“已触发”。

## CX06 Plugin来源

### 目标

用 CLI 状态区分 marketplace、缓存、安装、启用与当前任务可用。

### 只读验证

```sh
codex plugin list \
  | python3 -c 'import os, sys; print(sys.stdin.read().replace(os.path.expanduser("~"), "$HOME"), end="")' \
  | sed -n '1,120p'
```

### 观察要点

- 同一市场快照可以同时列出 `installed, enabled` 与 `not installed`。
- PATH 列出现缓存位置只证明来源可发现，不能覆盖 STATUS 的结论。
- 安装后的 Skills 通常要在新任务或新会话观察；Apps、MCP 与 Hooks 还可能分别要求连接认证、权限设置和信任审查。

### 通过标准

输出中的主目录已替换成 `$HOME`。能够任选一个已安装项和一个未安装项，分别指出其 STATUS；不读取插件脚本或缓存内容。

## CX07 MCP权限

### 目标

只观察 MCP 登记和权限键，建立最小工具面、最小审批与最小授权范围。

### 只读验证

```sh
codex mcp --help

sed -n -E \
  -e 's/^\[mcp_servers\.([A-Za-z0-9_-]+).*/server:\1/p' \
  -e 's/^[[:space:]]*(enabled|enabled_tools|disabled_tools|default_tools_approval_mode|approval_mode|bearer_token_env_var|env_vars)[[:space:]]*=.*$/key:\1/p' \
  "$HOME/.codex/config.toml" | sort -u
```

### 观察要点

- `[mcp_servers.<id>]` 只证明配置登记；enabled、初始化、认证、工具过滤和当前任务暴露仍需分别确认。
- `enabled_tools` 建立允许集，`disabled_tools` 在其后继续拒绝；默认和单工具审批模式控制调用交互。
- `env` 与 `env_vars` 会把环境材料转交给 stdio 服务器。只记录变量名或配置键，不显示值。
- 远程认证优先使用 OAuth、系统凭证或环境变量引用，并申请最小 scopes。

### 通过标准

只得到 MCP 帮助、服务器标识和权限相关键名，没有 URL、请求头、环境值或认证值。能为只读文档服务器提出 search/read 白名单。

## CX08 Hook与Rules

### 目标

确认 Hook 信任、可观察失败和 Rules 对 shell wrapper 的边界。

### 只读验证

```sh
codex --help | rg 'hook|approval|sandbox'
codex execpolicy check --help | sed -n '1,120p'

sed -n -E 's/^\[hooks.*/hook_table/p' "$HOME/.codex/config.toml" \
  | sort \
  | uniq -c

RULE_FILE="$(mktemp "${TMPDIR:-/tmp}/codex-course-rule.XXXXXX")"
trap 'rm -f "$RULE_FILE"' EXIT HUP INT TERM
cat >"$RULE_FILE" <<'RULE'
prefix_rule(
    pattern = ["git", "status"],
    decision = "prompt",
    match = ["git status", "git status --short"],
    not_match = ["git push"],
)
RULE
codex execpolicy check --pretty --rules "$RULE_FILE" -- git status
codex execpolicy check --pretty --rules "$RULE_FILE" -- git push
rm -f "$RULE_FILE"
trap - EXIT HUP INT TERM
```

然后在当前 Codex 任务打开 `/hooks`，只观察来源、待审查、受信任或禁用状态，不改变信任决定。

### 观察要点

- 非托管 Hook 的信任绑定当前定义哈希；新增或变更后，未审查会被跳过。安装插件不会自动信任其 Hook。
- 当前只运行 `command` handler；已解析但不受支持的 handler 可能被跳过。退出 0 且无输出会被当作成功，因此沉默不等于检查正确。
- Rules 按 argv 前缀匹配。简单线性脚本可拆分，含重定向、替换、变量、通配符或控制流的脚本会作为完整 wrapper 调用评估。
- 不应宽泛允许 `bash -lc`、`bash -c` 或同类 shell wrapper；复杂内部脚本会成为规则盲区。
- 临时规则的 `match`/`not_match` 是加载时向量；两次 `execpolicy check` 只计算规则，不执行 `git status` 或 `git push`，预期分别得到 `prompt` 与无匹配。

### 通过标准

只读命令没有执行 Hook 或改变规则。能够说明为什么“已配置”“已信任”“运行成功”“实际阻断”是四条不同证据。

## CX09 Subagent自动化

### 目标

区分单次并行委派、持续目标、记忆能力与按时间运行的 Scheduled task。

### 只读验证

```sh
codex features list \
  | rg '^(goals|hooks|memories|multi_agent|plugins)[[:space:]]'
```

在桌面应用中只观察 Subagents 与 Scheduled 入口及其当前空状态，不创建对象。当前脱敏快照没有 Memory、Goal 或 Automation 数据；这条记录不否定对应能力存在。

### 观察要点

- Subagent 适合一个任务内彼此独立的探索、测试、审查和汇总；它默认继承父任务沙箱并消耗额外资源，自定义 agent 配置可显式覆写 `sandbox_mode`。
- Scheduled task 负责无人值守按时间启动；同一任务持续跟进与每次独立运行是两种不同调度方式。
- Goal 记录持续目标，Memory 提供可选回忆，二者都不是定时器。
- Full Access + Never 用于无人值守任务时风险更高，应优先只读或工作区写入、隔离工作树和最小网络。

### 通过标准

终端只显示功能名、成熟度与布尔状态；界面观察只记录“入口存在”和“当前无数据”。没有读取任何对象正文或本地状态库。

## CX10 场景化诊断

### 目标

用六类证据维度定位“明明配置了却不能用”，并生成可分享的最小脱敏快照；不适用于某类能力的维度明确标 `N/A`。

### 只读验证

```sh
printf '%s\n' '== version =='
codex --version

printf '%s\n' '== feature surface =='
codex features list \
  | rg '^(goals|hooks|memories|multi_agent|plugins)[[:space:]]'

printf '%s\n' '== plugin lifecycle =='
codex plugin list \
  | python3 -c 'import os, sys; print(sys.stdin.read().replace(os.path.expanduser("~"), "$HOME"), end="")' \
  | rg '^(PLUGIN|[-A-Za-z0-9@_.]+[[:space:]]+(installed|not installed))' \
  | sed -n '1,60p'

printf '%s\n' '== registered structures =='
sed -n -E \
  -e 's/^\[(plugins|mcp_servers|hooks|features|memories)(\..*)?\]$/table:\1/p' \
  -e 's/^[[:space:]]*(enabled|enabled_tools|disabled_tools|approval_mode)[[:space:]]*=.*$/key:\1/p' \
  "$HOME/.codex/config.toml" | sort -u
```

### 六维证据矩阵

| 维度 | 最小证据 | 常见 `N/A` |
|---|---|---|
| 磁盘存在 | 脱敏路径或 yes/no | 远程 HTTP MCP 没有本地实现目录 |
| 配置登记 | 表名、键名或启用覆盖 | 未写 `skills.config` 的直接 Skill |
| 安装/来源 | Plugin STATUS 或正式来源记录 | 直接 Skill 与普通 MCP 没有插件安装步骤 |
| 当前任务可用 | 当前工具或能力目录 | 能力未面向当前产品表面 |
| 模型可见 | Skill 元数据或工具说明进入任务 | 只供 UI 使用、不进入模型上下文的表面 |
| 使用证据 | 明确的工具结果或流程产物 | 尚未做最小调用时是“缺证据”，不是 `N/A` |

这六列是取证清单，不是所有扩展必经的单一状态链。直接 Skill 可把“配置登记”和“安装”标为 `N/A`；普通 MCP 可把“插件安装”标为 `N/A`，改查初始化、认证和工具过滤；Plugin 则应保留正式安装状态。`N/A` 表示机制不适用，“no”或空白才表示适用但尚未证明。

### 诊断顺序

1. 先确定能力类型，为机制不适用的列标 `N/A`。
2. 对适用列确认版本、磁盘候选、配置登记、enabled 与最小权限键，不读取正文。
3. Plugin 用正式 STATUS；MCP 查初始化与认证；直接 Skill 查扫描来源，不以缓存互相替代。
4. 配置变化后开启新任务，检查当前工具和 Skill 目录。
5. 用一条最小只读调用取得使用证据；未调用记“缺证据”，不能标 `N/A`。
6. 报告空状态时写“当前无数据”，不要写“无能力”。

### 通过标准

能先区分 `N/A` 与缺证据，再把任一故障停在适用的准确维度并指出下一条最小证据。输出不含 secret、个人绝对路径或运行态正文，所有主目录均显示为 `$HOME`。
