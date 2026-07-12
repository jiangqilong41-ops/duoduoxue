# 通用 Agent Harness：Mac 实验手册

本手册基于 `shareAI-lab/learn-claude-code@a9cafe953aa714f9cb1171f217d96bd2734bbcc7` 的通用机制重新编写。请让 Codex 在同一个 Mac 终端会话中协助执行；所有实验只使用 Python 标准库、固定响应和模拟工具，不需要网络或 API Key。实验目录由 `mktemp -d` 原子创建，每次运行独占一份。

## 会话初始化

先执行一次下列命令。`mktemp -d` 不复用预存路径；目录守卫会拒绝符号链接或丢失的目录。后续代码块若换了终端会话会直接失败，不会回退到固定路径。

```sh
umask 077
AGENT_LAB_PARENT="$(cd -- "${TMPDIR:-/tmp}" && pwd -P)" || exit 1
AGENT_LAB_ROOT="$(mktemp -d "${AGENT_LAB_PARENT%/}/duoduoxue-agent-lab.XXXXXXXX")" || exit 1
export AGENT_LAB_ROOT
agent_lab_cd() {
  if [ -z "${AGENT_LAB_ROOT:-}" ] || [ ! -d "$AGENT_LAB_ROOT" ] || [ -L "$AGENT_LAB_ROOT" ]; then
    printf '%s\n' '实验目录不存在或不是可信的普通目录' >&2
    return 1
  fi
  cd -- "$AGENT_LAB_ROOT"
}
agent_lab_cd || exit 1
printf 'lab=%s\n' "$AGENT_LAB_ROOT"
```

## AG01 Agent边界

### 目标

区分模型负责的决策与 Harness 负责的环境、工具和强制边界，验证“模型提出动作，Harness 决定能否执行”。

### 步骤

1. 让 Codex 创建临时实验目录并运行脚本。
2. 观察同一个写入意图如何经过边界检查，但不执行真实写入。
3. 对照输出判断哪一层负责提出动作，哪一层负责阻止越界。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
import os
from pathlib import Path

lab_root = Path(os.environ["AGENT_LAB_ROOT"]).resolve(strict=True)
workspace = lab_root / "ag01-workspace"
workspace.mkdir()
model_action = {"tool": "write", "path": str(lab_root / "outside.txt")}
target = Path(model_action["path"]).resolve()
allowed = target.is_relative_to(workspace)
print("model=propose:write")
print(f"harness={'allow' if allowed else 'block:outside-workspace'}")
print("target_exists=" + str(target.exists()))
PY
```

### 通过标准

终端依次出现 `model=propose:write`、`harness=block:outside-workspace` 与 `target_exists=False`。目标位于本次独占实验目录内、AG01 子工作区外，因此结果不依赖机器上某个固定 `/tmp` 文件是否预先存在。

### 恢复/清理

本节只创建空的 AG01 子工作区，不创建目标文件；保留本次实验目录供后续实验复用即可。

## AG02 Agent循环

### 目标

观察最小 Agent 循环的两种出口：有工具请求时执行并把结果送回循环，无工具请求时返回最终文本。

### 步骤

1. 运行固定的两轮模型响应。
2. 确认第一轮工具结果被追加到消息历史。
3. 确认第二轮没有工具请求，因此循环停止。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
responses = iter([
    {"tool_calls": [{"id": "t1", "name": "read", "args": {"path": "note.txt"}}]},
    {"text": "done", "tool_calls": []},
])
messages = [{"role": "user", "content": "inspect note"}]

for turn in range(1, 4):
    response = next(responses)
    messages.append({"role": "assistant", **response})
    if not response["tool_calls"]:
        print(f"turn{turn}=final:{response['text']};history={len(messages)}")
        break
    call = response["tool_calls"][0]
    result = "demo-content"
    messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    print(f"turn{turn}=execute:{call['name']};history={len(messages)}")

request_ids = [
    call["id"]
    for message in messages if message["role"] == "assistant"
    for call in message["tool_calls"]
]
result_ids = [message["tool_call_id"] for message in messages if message["role"] == "tool"]
paired = request_ids == result_ids == ["t1"]
closed = messages[-1]["role"] == "assistant" and not messages[-1]["tool_calls"]
print("paired=" + str(paired))
print("closed=" + str(closed))
PY
```

### 通过标准

输出包含 `turn1=execute:read;history=3`、`turn2=final:done;history=4`、`paired=True` 和 `closed=True`，且没有第三轮输出。四条历史依次是用户输入、assistant 工具请求、对应工具结果和 assistant 最终响应。

### 恢复/清理

状态仅存在于 Python 进程内；脚本退出后自动清空，无需删除文件。

## AG03 工具契约

### 目标

验证工具定义、参数校验、分发表和结果封装形成稳定契约，新增工具不需要改动主循环。

### 步骤

1. 用带参数类型的工具定义组装分发表。
2. 覆盖合法参数、非对象参数、缺键、多余键、错误类型、未知工具和处理器异常。
3. 用断言确认所有失败都返回统一的结构化错误，且脚本不中断。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
TOOLS = {
    "add": ({"a": int, "b": int}, lambda a, b: a + b),
    "upper": ({"text": str}, lambda text: text.upper()),
    "fail": ({}, lambda: (_ for _ in ()).throw(RuntimeError("demo"))),
}

def error(code, fields=()):
    return {"ok": False, "error": {"code": code, "fields": list(fields)}}

def dispatch(call):
    if not isinstance(call, dict):
        return error("invalid-call")
    spec = TOOLS.get(call.get("name"))
    if spec is None:
        return error("unknown-tool")
    schema, handler = spec
    args = call.get("args")
    if not isinstance(args, dict):
        return error("invalid-args")
    missing = sorted(schema.keys() - args.keys())
    if missing:
        return error("missing", missing)
    extra = sorted(args.keys() - schema.keys())
    if extra:
        return error("extra", extra)
    wrong = sorted(name for name, expected in schema.items() if type(args[name]) is not expected)
    if wrong:
        return error("wrong-type", wrong)
    try:
        return {"ok": True, "value": handler(**args)}
    except Exception as exc:
        return error("handler-error", [type(exc).__name__])

cases = {
    "valid": {"name": "add", "args": {"a": 2, "b": 3}},
    "not-object": {"name": "add", "args": [2, 3]},
    "missing": {"name": "upper", "args": {}},
    "extra": {"name": "upper", "args": {"text": "hi", "locale": "en"}},
    "wrong-type": {"name": "add", "args": {"a": "2", "b": 3}},
    "handler-error": {"name": "fail", "args": {}},
    "unknown": {"name": "search", "args": {}},
}
results = {label: dispatch(call) for label, call in cases.items()}
assert results["valid"] == {"ok": True, "value": 5}
expected_codes = {
    "not-object": "invalid-args", "missing": "missing", "extra": "extra",
    "wrong-type": "wrong-type", "handler-error": "handler-error", "unknown": "unknown-tool",
}
assert all(results[label]["error"]["code"] == code for label, code in expected_codes.items())
assert results["handler-error"]["error"]["fields"] == ["RuntimeError"]
for label, result in results.items():
    outcome = "ok:5" if result["ok"] else result["error"]["code"]
    print(f"{label}={outcome}")
PY
```

### 通过标准

合法调用输出 `valid=ok:5`；其余分支依次输出 `invalid-args`、`missing`、`extra`、`wrong-type`、`handler-error` 与 `unknown-tool`。断言证明这些失败都经过同一个结构化错误封装，处理器异常也没有使脚本异常退出。

### 恢复/清理

本节没有持久化状态；脚本退出即恢复。

## AG04 权限边界

### 目标

观察本课程示例采用的“拒绝优先、询问其次、默认放行”顺序，并确认检查发生在工具处理器之前。该顺序用于演示三态冲突处理，不是所有产品唯一的通用策略；真实系统应按风险模型配置，也可对越界写入直接拒绝。

### 步骤

1. 运行三类模拟动作：只读、工作区外写入、高风险系统动作。
2. 记录权限决策，不调用任何真实系统工具。
3. 确认高风险动作不会被后续审批覆盖。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
def permission(action):
    if action["kind"] == "system_reset":
        return "deny"
    if action.get("outside_workspace"):
        return "ask"
    return "allow"

actions = [
    {"name": "inspect", "kind": "read"},
    {"name": "external-write", "kind": "write", "outside_workspace": True},
    {"name": "reset", "kind": "system_reset", "outside_workspace": True},
]
for action in actions:
    print(f"{action['name']}={permission(action)}")
PY
```

### 通过标准

按本课程示例策略，输出严格为 `inspect=allow`、`external-write=ask`、`reset=deny`；最后一项即使命中询问条件也保持拒绝。

### 恢复/清理

本节只模拟决策，不执行动作，也不产生文件。

## AG05 Hook扩展

### 目标

在不改主循环的前提下，用执行前 Hook 拦截动作、用执行后 Hook 记录结果，并观察短路行为。

### 步骤

1. 注册两个执行前 Hook 和一个执行后 Hook。
2. 依次提交 `read` 与 `external-write` 模拟动作。
3. 比较允许路径与拦截路径的事件记录。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
hooks = {"pre": [], "post": []}
events = []

hooks["pre"].append(lambda action: "blocked" if action == "external-write" else None)
hooks["pre"].append(lambda action: events.append("audit:" + action))
hooks["post"].append(lambda action, result: events.append("post:" + result))

def run(action):
    for hook in hooks["pre"]:
        verdict = hook(action)
        if verdict is not None:
            return verdict
    result = "ok"
    for hook in hooks["post"]:
        hook(action, result)
    return result

print("read=" + run("read"))
print("external-write=" + run("external-write"))
print("events=" + ",".join(events))
PY
```

### 通过标准

`read=ok`，`external-write=blocked`；事件中有 `audit:read` 和 `post:ok`，但没有被拦截动作的 post 事件。

### 恢复/清理

Hook 注册表和事件仅在内存中，进程退出后自动恢复。

## AG06 计划与任务

### 目标

观察任务依赖状态如何改变就绪列表，并核对任务状态已写入临时 JSON。本实验不模拟真正的任务认领、协作恢复或并发所有权。

### 步骤

1. 建立两个带依赖的任务并写入临时 JSON。
2. 在完成上游前后分别计算就绪任务。
3. 用 `json.tool` 只读检查最终状态。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["AGENT_LAB_ROOT"]) / "ag06-tasks.json"
tasks = {
    "T1": {"status": "pending", "deps": []},
    "T2": {"status": "pending", "deps": ["T1"]},
}

def ready():
    return [name for name, task in tasks.items()
            if task["status"] == "pending"
            and all(tasks[dep]["status"] == "completed" for dep in task["deps"])]

print("before=" + ",".join(ready()))
tasks["T1"]["status"] = "completed"
print("after=" + ",".join(ready()))
path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
PY
python3 -m json.tool "$AGENT_LAB_ROOT/ag06-tasks.json"
```

### 通过标准

完成上游前输出 `before=T1`，完成后输出 `after=T2`；JSON 中 `T1` 为 `completed`、`T2` 仍为 `pending`。

### 恢复/清理

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
import os
from pathlib import Path

(Path(os.environ["AGENT_LAB_ROOT"]) / "ag06-tasks.json").unlink(missing_ok=True)
PY
```

## AG07 Skill知识

### 目标

观察两级加载：先把 Skill 名称和摘要放入上下文，只有选中后才加载完整正文。

### 步骤

1. 创建两个内存 Skill 条目。
2. 先打印目录摘要，再按任务选择一个 Skill。
3. 检查最终上下文没有包含未选择 Skill 的正文。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
skills = {
    "csv": {"summary": "处理表格文本", "body": "使用 csv 标准库并校验列数"},
    "http": {"summary": "读取网页资源", "body": "设置超时并检查状态码"},
}
catalog = [f"{name}:{item['summary']}" for name, item in skills.items()]
selected = "csv"
context = {"catalog": catalog, "loaded": skills[selected]["body"]}
print("catalog=" + "|".join(context["catalog"]))
print("loaded=" + context["loaded"])
print("http_body_present=" + str(skills["http"]["body"] in str(context)))
PY
```

### 通过标准

目录同时列出 `csv` 与 `http`，`loaded` 只出现 csv 正文，最后输出 `http_body_present=False`。

### 恢复/清理

本节没有创建 Skill 文件，所有材料随进程退出而清空。

## AG08 子Agent隔离

### 目标

验证子 Agent 只接收任务所需的干净上下文，完成后只把摘要返回父 Agent，不回灌完整过程。

### 步骤

1. 构造包含噪声的父上下文。
2. 从任务和必要事实组装子上下文。
3. 将子 Agent 的多步轨迹压成一条摘要返回父级。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
parent = ["user:build report", "tool:large unrelated log", "fact:format=json"]
child = [parent[0], parent[2]]
child_trace = ["inspect schema", "validate fields", "result:valid"]
summary = child_trace[-1]
parent.append("subagent:" + summary)
print("child_items=" + str(len(child)))
print("noise_in_child=" + str(any("unrelated" in item for item in child)))
print("trace_returned=" + str(any("inspect schema" in item for item in parent)))
print("summary=" + parent[-1])
PY
```

### 通过标准

输出 `child_items=2`、`noise_in_child=False`、`trace_returned=False`，父级只收到 `subagent:result:valid`。

### 恢复/清理

父子上下文均为内存列表，脚本结束后无需清理。

## AG09 上下文压缩

### 目标

用短占位符替换一个旧工具大结果，验证字符数下降、工具调用仍配对且最近消息未改写。本实验不验证多层压缩顺序或全局摘要。

### 步骤

1. 构造一段含旧工具大结果的历史。
2. 将旧结果替换为可识别占位符，保留调用 ID。
3. 检查调用 ID 仍配对且最近消息未改写。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
history = [
    {"role": "user", "content": "goal: inspect project"},
    {"role": "assistant", "tool_call_id": "t1", "content": "call:scan"},
    {"role": "tool", "tool_call_id": "t1", "content": "x" * 200},
    {"role": "user", "content": "keep the latest request"},
]
before = sum(len(item["content"]) for item in history)
history[2]["content"] = "[old tool result omitted]"
after = sum(len(item["content"]) for item in history)
paired = history[1]["tool_call_id"] == history[2]["tool_call_id"]
print(f"chars={before}->{after}")
print("paired=" + str(paired))
print("latest=" + history[-1]["content"])
PY
```

### 通过标准

字符数明显下降，`paired=True`，最后仍输出 `latest=keep the latest request`。

### 恢复/清理

压缩对象只存在于内存；脚本退出后恢复为空状态。

## AG10 记忆与Prompt

### 目标

区分长期记忆筛选与运行时 Prompt 组装，验证只注入当前任务相关记忆和当前模式所需分段。

### 步骤

1. 准备两条候选记忆与真实运行上下文。
2. 按任务标签筛选记忆。
3. 根据上下文布尔字段拼接 Prompt 分段。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
memories = [
    {"tag": "python", "text": "项目要求使用标准库"},
    {"tag": "design", "text": "界面使用紧凑布局"},
]
context = {"task_tag": "python", "has_tools": True, "team_mode": False}
selected = [m["text"] for m in memories if m["tag"] == context["task_tag"]]
sections = ["identity", "boundaries"]
if context["has_tools"]:
    sections.append("tools")
if context["team_mode"]:
    sections.append("team")
print("memory=" + "|".join(selected))
print("prompt=" + ",".join(sections))
PY
```

### 通过标准

只输出 Python 相关记忆；Prompt 分段为 `identity,boundaries,tools`，不含 `team`。

### 恢复/清理

候选记忆与 Prompt 都在内存中，进程退出即清理。

## AG11 错误恢复

### 目标

按错误类型选择恢复路径：上下文超限先压缩，临时故障有限重试，不可恢复错误立即返回。

### 步骤

1. 分别运行立即成功、压缩与退避后成功、临时故障耗尽和不可恢复错误四组序列。
2. 记录每次恢复动作与确定性的指数退避值，不实际等待。
3. 断言成功会停止、耗尽会失败、不可恢复错误只尝试一次。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
def recover(outcomes, max_attempts=3):
    trace = []
    retries = 0
    for attempt, outcome in enumerate(outcomes[:max_attempts], start=1):
        if outcome == "success":
            trace.append(f"{attempt}:return")
            return {"status": "ok", "attempts": attempt, "trace": trace}
        if outcome == "fatal":
            trace.append(f"{attempt}:fail:fatal")
            return {"status": "error:fatal", "attempts": attempt, "trace": trace}
        if outcome == "context_overflow":
            trace.append(f"{attempt}:compact")
            continue
        if outcome == "transient" and attempt < max_attempts:
            delay = 2 ** retries
            retries += 1
            trace.append(f"{attempt}:retry:backoff={delay}")
            continue
        trace.append(f"{attempt}:fail:retry-exhausted")
        return {"status": "error:retry-exhausted", "attempts": attempt, "trace": trace}
    return {"status": "error:attempts-exhausted", "attempts": len(trace), "trace": trace}

cases = {
    "success": ["success"],
    "recovered": ["context_overflow", "transient", "success"],
    "exhausted": ["transient", "transient", "transient"],
    "fatal": ["fatal", "success"],
}
results = {name: recover(outcomes) for name, outcomes in cases.items()}
assert results["success"]["status"] == "ok" and results["success"]["attempts"] == 1
assert results["recovered"]["trace"] == ["1:compact", "2:retry:backoff=1", "3:return"]
assert results["exhausted"]["status"] == "error:retry-exhausted"
assert results["exhausted"]["trace"][-1] == "3:fail:retry-exhausted"
assert results["fatal"]["status"] == "error:fatal" and results["fatal"]["attempts"] == 1
for name, result in results.items():
    print(f"{name}={result['status']};attempts={result['attempts']};trace={'|'.join(result['trace'])}")
PY
```

### 通过标准

四行输出分别证明：立即成功只调用一次；恢复路径为 `1:compact|2:retry:backoff=1|3:return`；耗尽路径以 `3:fail:retry-exhausted` 结束；不可恢复路径为 `1:fail:fatal` 且 `attempts=1`。所有路径最多尝试三次。

### 恢复/清理

故障序列与重试计数只在内存中，不需要额外清理。

## AG12 后台与调度

### 目标

观察慢任务与主循环解耦、调度器按固定时刻入队、每个唯一作业在同一分钟只触发一次，并把后台完成通知重新注入模型历史。

### 步骤

1. 用固定时钟模拟三个 tick，不等待真实时间。
2. 将两个同名但 ID 不同的到期作业放入标准库队列，再交给后台线程执行器。
3. 主循环在任务等待时继续记录前台消息，随后把完成通知回注历史并只读检查临时状态。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from queue import Empty, Queue
from threading import Event

ticks = ["2026-07-11 09:00", "2026-07-11 09:00", "2026-07-11 09:01"]
jobs = [
    {"id": "job-001", "minute": "09:00", "task": "refresh-index"},
    {"id": "job-002", "minute": "09:00", "task": "refresh-index"},
]
scheduled = Queue()
seen = set()
for tick in ticks:
    for job in jobs:
        marker = (job["id"], tick)
        if tick.endswith(job["minute"]) and marker not in seen:
            seen.add(marker)
            scheduled.put(job)

started = Queue()
release = Event()

def execute(job):
    started.put(job["id"])
    if not release.wait(timeout=2):
        raise TimeoutError("foreground did not release background jobs")
    return {"job_id": job["id"], "task": job["task"], "status": "completed"}

history = [{"role": "user", "content": "schedule refresh"}]
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = []
    while True:
        try:
            futures.append(executor.submit(execute, scheduled.get_nowait()))
        except Empty:
            break
    started_ids = sorted(started.get(timeout=2) for _ in futures)
    history.append({"role": "assistant", "content": "foreground-continued"})
    release.set()
    notifications = sorted((future.result(timeout=2) for future in futures), key=lambda item: item["job_id"])

for notification in notifications:
    history.append({"role": "system", "kind": "background_notification", **notification})

injected_ids = [item["job_id"] for item in history if item.get("kind") == "background_notification"]
assert started_ids == ["job-001", "job-002"]
assert injected_ids == started_ids
assert [item["task"] for item in notifications] == ["refresh-index", "refresh-index"]
assert history[1]["content"] == "foreground-continued"
path = Path(os.environ["AGENT_LAB_ROOT"]) / "ag12-state.json"
path.write_text(json.dumps({"history": history}, ensure_ascii=False, indent=2), encoding="utf-8")
print("trigger_count=" + str(len(notifications)))
same_name_jobs = len(set(injected_ids)) == 2 and len({item["task"] for item in notifications}) == 1
print("same_name_jobs=" + str(same_name_jobs))
print("foreground_continued=True")
print("injected=" + ",".join(injected_ids))
PY
python3 -m json.tool "$AGENT_LAB_ROOT/ag12-state.json"
```

### 通过标准

相同的 09:00 tick 没有重复触发每个作业，但两个同名、不同 ID 的作业都执行；输出 `trigger_count=2`、`same_name_jobs=True`、`foreground_continued=True` 与 `injected=job-001,job-002`。JSON 历史中前台消息位于两条后台完成通知之前。

### 恢复/清理

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
import os
from pathlib import Path

(Path(os.environ["AGENT_LAB_ROOT"]) / "ag12-state.json").unlink(missing_ok=True)
PY
```

## AG13 MCP工具池

### 目标

模拟外部服务的工具发现，将安全名称加入内置工具池，并显式拒绝规范化后发生的服务名或工具名碰撞。

### 步骤

1. 先用两个无碰撞的模拟服务组装带命名空间的工具池。
2. 再分别加入 `docs team`/`docs_team` 与 `create ticket`/`create_ticket` 碰撞样例。
3. 检查安全工具池唯一，两个碰撞样例都在注册阶段被拒绝。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
import re

def safe(name):
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)

def build_pool(servers):
    pool = ["read_file"]
    server_names = {}
    for raw_server, tools in servers:
        server = safe(raw_server)
        if server in server_names:
            raise ValueError("normalized-name-collision:server:" + server)
        server_names[server] = raw_server
        tool_names = set()
        for raw_tool in tools:
            tool = safe(raw_tool)
            if tool in tool_names:
                raise ValueError(f"normalized-name-collision:tool:{server}:{tool}")
            tool_names.add(tool)
            pool.append(f"mcp__{server}__{tool}")
    if len(pool) != len(set(pool)):
        raise ValueError("final-name-collision")
    return pool

pool = build_pool([("docs team", ["search"]), ("issues", ["search", "create ticket"])])
print("pool=" + ",".join(sorted(pool)))
print("unique=" + str(len(pool) == len(set(pool))))
fixtures = {
    "server_collision": [("docs team", ["search"]), ("docs_team", ["lookup"])],
    "tool_collision": [("issues", ["create ticket", "create_ticket"])],
}
for label, servers in fixtures.items():
    try:
        build_pool(servers)
    except ValueError as exc:
        print(f"{label}=rejected:{exc}")
    else:
        raise AssertionError(label + " was not rejected")
PY
```

### 通过标准

安全工具池包含 `read_file`、`mcp__docs_team__search`、`mcp__issues__search` 和 `mcp__issues__create_ticket`，并输出 `unique=True`。另外两行分别输出 `server_collision=rejected:normalized-name-collision:server:docs_team` 与 `tool_collision=rejected:normalized-name-collision:tool:issues:create_ticket`。

### 恢复/清理

服务与工具池均为本地模拟数据，没有启动进程或建立网络连接；退出即清理。

## AG14 多Agent综合

### 目标

把任务依赖、锁保护的唯一认领与状态变更、隔离上下文和消息回传放进一个真实并发的本地模拟中。

### 步骤

1. 建立三项任务，其中汇总任务依赖两个并行任务。
2. 为两个 Agent 创建独立上下文和目录，用标准库线程并发争用任务。
3. 在锁内完成认领与状态变更，验证每项只认领一次、汇总任务在依赖完成后出现。

### 只读/临时命令

```sh
agent_lab_cd || exit 1
python3 - <<'PY'
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
from threading import Barrier, Lock

root = Path(os.environ["AGENT_LAB_ROOT"])
tasks = {
    "inspect": {"deps": [], "status": "pending", "owner": None},
    "test": {"deps": [], "status": "pending", "owner": None},
    "report": {"deps": ["inspect", "test"], "status": "pending", "owner": None},
}
contexts = {agent: {"workspace": root / f"ag14-{agent.lower()}"} for agent in ("A", "B")}
for context in contexts.values():
    context["workspace"].mkdir()

inbox = []
claims = []
events = []
lock = Lock()
start = Barrier(3)
leaves_done = Barrier(2)

def claim(agent):
    with lock:
        for name, task in tasks.items():
            ready = all(tasks[dep]["status"] == "completed" for dep in task["deps"])
            if task["status"] == "pending" and ready:
                task.update(status="in_progress", owner=agent)
                claims.append((name, agent))
                events.append(("claim", name))
                return name
    return None

def complete(agent, name, output):
    with lock:
        task = tasks[name]
        assert task["status"] == "in_progress" and task["owner"] == agent
        task["status"] = "completed"
        inbox.append({"agent": agent, "task": name, "output": output})
        events.append(("complete", name))

def run_agent(agent):
    workspace = contexts[agent]["workspace"]
    start.wait()
    leaf = claim(agent)
    assert leaf in {"inspect", "test"}
    leaf_output = workspace / f"{leaf}.txt"
    leaf_output.write_text(f"{agent}:{leaf}:done", encoding="utf-8")
    complete(agent, leaf, leaf_output)
    leaves_done.wait()
    report = claim(agent)
    if report is not None:
        with lock:
            evidence = sorted(item["task"] for item in inbox if item["task"] in {"inspect", "test"})
        report_output = workspace / "report.txt"
        report_output.write_text(",".join(evidence), encoding="utf-8")
        complete(agent, report, report_output)

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(run_agent, agent) for agent in contexts]
    start.wait()
    for future in futures:
        future.result(timeout=3)

claim_counts = Counter(name for name, _ in claims)
unique_claims = claim_counts == Counter({"inspect": 1, "test": 1, "report": 1})
leaf_owners = {tasks[name]["owner"] for name in ("inspect", "test")}
report_claim = events.index(("claim", "report"))
report_after_dependencies = all(events.index(("complete", name)) < report_claim for name in ("inspect", "test"))
atomic_transitions = all(
    events.index(("claim", name)) < events.index(("complete", name)) for name in tasks
)
isolated = len({context["workspace"] for context in contexts.values()}) == 2 and all(
    item["output"].is_relative_to(contexts[item["agent"]]["workspace"]) for item in inbox
)
assert unique_claims and len(leaf_owners) == 2 and report_after_dependencies
assert atomic_transitions and isolated and len(inbox) == 3
print("unique_claims=True")
print("leaf_owners_distinct=True")
print("report_after_dependencies=True")
print("atomic_transitions=True")
print("isolated=True")
print("messages=3")
print("all_completed=" + str(all(task["status"] == "completed" for task in tasks.values())))
PY
```

### 通过标准

输出 `unique_claims=True`、`leaf_owners_distinct=True`、`report_after_dependencies=True`、`atomic_transitions=True`、`isolated=True`、`messages=3` 和 `all_completed=True`。由于是真实并发，具体哪个 Agent 拿到哪项任务不作为通过条件。

### 恢复/清理

综合实验只修改本次独占目录。完成全部实验后，运行以下守卫化清理；它只接受本次 `mktemp` 目录的名称模式，并拒绝符号链接：

```sh
agent_lab_cd || exit 1
LAB_TO_DELETE="$AGENT_LAB_ROOT"
cd -- "$AGENT_LAB_PARENT" || exit 1
case "$LAB_TO_DELETE" in
  "$AGENT_LAB_PARENT"/duoduoxue-agent-lab.*) ;;
  *) printf '%s\n' '拒绝清理非本次实验目录' >&2; exit 1 ;;
esac
if [ ! -d "$LAB_TO_DELETE" ] || [ -L "$LAB_TO_DELETE" ]; then
  printf '%s\n' '拒绝清理丢失目录或符号链接' >&2
  exit 1
fi
rm -rf -- "$LAB_TO_DELETE"
printf 'removed=%s\n' "$LAB_TO_DELETE"
unset AGENT_LAB_ROOT LAB_TO_DELETE
unset -f agent_lab_cd
```
