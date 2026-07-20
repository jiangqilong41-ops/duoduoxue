# 看懂 fastapi1：Mac 实验手册

本手册只观察 `$HOME/Documents/fastapi1` 在提交 `710807b` 的已提交源码。不要读取 `.env`、数据库、导出文件、客户数据、用户级凭据或本地运行状态，也不要调用生产或其他远程服务。

每课开始都先运行：

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git rev-parse --verify '710807b^{commit}'
```

若 `git status --short` 有输出，停止分支练习，不覆盖或清理现有改动。只读的 `git show`、`git grep` 和 `git ls-tree` 仍应固定在 `710807b`。需要持续改造时，确认工作区为空后从 `710807b` 创建本课独立分支；回滚命令仅可用于该分支中由自己改动且已经逐行检查过的明确路径。

执行本手册的本地测试前，在仓库根定义以下两个临时 helper。它们只把 Git 已跟踪文件复制到一次性 `tracked_snapshot`，因此不会带入未跟踪或忽略的 `.env`、数据库、导出与运行态文件；若敏感文件已经被 Git 跟踪则直接拒绝运行。测试还会清空继承环境、禁用 dotenv 与字节码/pytest 缓存，并通过 macOS 系统沙箱拒绝包括 loopback 在内的全部网络；结束后删除整个临时目录。

```bash
safe_python() {
  local source_root python_bin test_root test_home tracked_snapshot exit_code sandbox_profile
  source_root="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  git -C "$source_root" merge-base --is-ancestor 710807b HEAD || {
    printf 'refuse: HEAD is not based on 710807b\n' >&2
    return 1
  }
  python_bin="$source_root/.venv/bin/python"
  test -x "$python_bin" || {
    printf 'refuse: project venv python is unavailable\n' >&2
    return 1
  }
  if git -C "$source_root" ls-files | awk '
    /(^|\/)\.env($|\.)/ && $0 !~ /\.env\.example$/ { found=1 }
    /\.(db|sqlite|sqlite3)(-|$)/ { found=1 }
    END { exit found ? 0 : 1 }
  '; then
    printf 'refuse: a sensitive runtime file is tracked\n' >&2
    return 1
  fi

  test_root="$(mktemp -d)" || return 1
  test_home="$test_root/home"
  tracked_snapshot="$test_root/tracked_snapshot"
  mkdir -p "$test_home" "$tracked_snapshot" || {
    rm -rf "$test_root"
    return 1
  }
  if ! (
    set -o pipefail
    git -C "$source_root" ls-files -z \
      | /usr/bin/tar -C "$source_root" --null -T - -cf - \
      | /usr/bin/tar -C "$tracked_snapshot" -xf -
  ); then
    rm -rf "$test_root"
    return 1
  fi

  sandbox_profile='(version 1)
(allow default)
(deny network*)'
  (
    cd "$tracked_snapshot" || exit 1
    env -i HOME="$test_home" PATH="$PATH" PYTHONPATH="$tracked_snapshot" \
      PYTHONNOUSERSITE=1 PYTHON_DOTENV_DISABLED=1 PYTHONDONTWRITEBYTECODE=1 \
      /usr/bin/sandbox-exec -p "$sandbox_profile" "$python_bin" "$@"
  )
  exit_code=$?
  rm -rf "$test_root"
  return "$exit_code"
}

safe_pytest() {
  safe_python -m pytest -p no:cacheprovider "$@"
}
```

## FA01 产品边界

### 目标

区分已经形成后端闭环的能力、只有页面或统计占位的能力，以及明确未完成的能力。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:README.md | rg -n '项目概述|当前运行入口|短信|电话|客户管理|AI 分析'
git show 710807b:main.py | rg -n 'include_router|mount\(|protected_html_page_guard'
git show 710807b:html/customer_management.html | rg -n '新增客户|暂未接入后端'
git show 710807b:html/Internet_marketing/Marketing_Management.html | rg -n '营销后端尚未实现'
git show 710807b:html/Internet_marketing/Sms_Marketing_Clean.html | rg -n '功能暂未接入后端'
git show 710807b:html/Internet_marketing/Telemarketing_Marketing_Clean.html | rg -n '功能暂未接入后端'
```

把能力分成三列：真实 API 与服务闭环、只读或占位页面、明确未完成。邮件、微信、查询导出、采集和 AI 应能找到后端证据；短信、电话营销和手工新增客户不能因为存在页面控件就标为完成。

### 可选分支练习

```bash
git switch -c course/fa01-product-boundary 710807b
```

只做一个小改动：在 `README.md` 补充一处能力状态说明，并在 `tests/test_documentation_governance.py` 锁定该事实，禁止顺便实现新渠道。

### 回滚

先确认下列两个路径只有本课改动，再执行：

```bash
git diff -- README.md tests/test_documentation_governance.py
git restore --staged -- README.md tests/test_documentation_governance.py
git restore --source=HEAD -- README.md tests/test_documentation_governance.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_customer_management_frontend.py -k 'add_customer'
safe_pytest -q tests/test_marketing_management_frontend.py
git diff --check
```

验收结论必须明确：短信、电话营销和手工新增客户后端仍未完成，除非本分支真的补齐了 API、服务与回归测试。

## FA02 组合根与生命周期

### 目标

画出 FastAPI 组合根的启动、就绪和关闭顺序，识别后台组件的所有者。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:main.py | rg -n 'lifespan|initialize_database_state|email_queue_worker|start_export_job_manager|_start_scheduler_if_primary|close_redis_client'
git show 710807b:main.py | rg -n 'include_router|add_middleware|mount\(|_collect_readiness_checks'
git show 710807b:app/enterprise_data_platform/api/routes.py | rg -n 'start_export_job_manager|stop_export_job_manager'
```

整理五列：组件、启动函数、停止函数、readiness 信号、失败后的可见行为。特别确认邮件消费者、导出管理器、SSE 线程池、Redis 客户端和单主调度器都有关闭路径。

### 可选分支练习

```bash
git switch -c course/fa02-lifecycle-map 710807b
```

选择一个只影响可观测性的微小改动，例如为已有生命周期分支补测试；不要在 import 时启动新线程。

### 回滚

```bash
git diff -- main.py tests/test_main_routes.py
git restore --staged -- main.py tests/test_main_routes.py
git restore --source=HEAD -- main.py tests/test_main_routes.py
git status --short
```

只有在确认这两个路径没有他人改动后才执行回滚。

### 验收

```bash
safe_pytest -q tests/test_main_routes.py tests/test_launch_readiness.py
git diff --check
```

验收时说明启动失败是否进入日志或 `/ready`，并证明关闭路径不会遗留本课新增资源。

## FA03 认证与权限

### 目标

识别 Bearer API、页面 cookie、X-Account-Key 客户端协议和邮件事件回调四类认证面，并与角色、区域权限分开理解。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:README.md | rg -n '权限控制|cli-token|access_token cookie|X-Account-Key|HMAC'
git show 710807b:app/middleware/permission.py | rg -n 'user_required|manager_required|admin_required|check_region_permission'
git show 710807b:app/login/routes.py | rg -n 'AUTH_TOKEN_COOKIE_NAME|/token|/cli-token|/me|/logout'
git show 710807b:app/internet_marketing/routes.py | rg -n 'HMAC|account.key|claim_next|report_wechat'
```

不要读取任何真实 key、token 或 cookie。为每类认证面记录凭据类型、适用入口、角色/区域限制、过期与撤销方式。

### 可选分支练习

```bash
git switch -c course/fa03-auth-review 710807b
```

只补一个拒绝路径测试，例如未认证、低角色或越区域；不要为了测试放宽默认认证。

### 回滚

```bash
git diff -- app/middleware/permission.py tests/test_permission_middleware.py
git restore --staged -- app/middleware/permission.py tests/test_permission_middleware.py
git restore --source=HEAD -- app/middleware/permission.py tests/test_permission_middleware.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_permission_middleware.py tests/test_login_security.py
git diff --check
```

至少覆盖合法身份、无凭据、低权限和区域越权四种情形；输出中不得含凭据或个人数据。

## FA04 数据与状态

### 目标

理解 PostgreSQL 持久业务真相、Redis 短期协调状态和 OSS 文档对象之间的边界。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:README.md | rg -n 'PostgreSQL|Redis|OSS|查询与导出|任务状态'
git show 710807b:app/utils/redis_client.py | rg -n '^def |redis|close'
git show 710807b:app/enterprise_data_platform/oss/oss_download.py | rg -n '^def |凭证|object|download|exists'
git grep -n 'SessionLocal\|get_redis_client\|download_from_oss' 710807b -- main.py app | sed -n '1,160p'
```

只记录调用关系，不连接任何存储。给每种状态标注真相源、TTL、恢复方式和访问控制。

### 可选分支练习

```bash
git switch -c course/fa04-state-boundaries 710807b
```

选一个现有 Redis 状态，补充“持久记录不存在时不得继续副作用”的测试；不要新增数据迁移。

### 回滚

```bash
git diff -- app/utils/redis_client.py tests/test_runtime_config.py
git restore --staged -- app/utils/redis_client.py tests/test_runtime_config.py
git restore --source=HEAD -- app/utils/redis_client.py tests/test_runtime_config.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_runtime_config.py tests/test_export_security.py
git diff --check
```

验收说明必须回答：Redis 清空后哪些业务能从持久层恢复，哪些能力应明确降级或失败。

## FA05 采集任务

### 目标

还原管理员创建任务、地区 item 领取、心跳续租、采集、数据同步和结果回传的 WebSocket 状态机。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:client/Data-Collection/README.md | rg -n 'WebSocket|租约|heartbeat|waiting|next_claim_after|退出码|sync_enterprise_data'
git show 710807b:app/index/project_collection_service.py | rg -n 'lease|heartbeat|waiting|next_claim_after|claim|result' | sed -n '1,200p'
git show 710807b:client/Data-Collection/main.py | rg -n 'request_task|heartbeat|sync_enterprise_data|waiting|result' | sed -n '1,200p'
git show 710807b:tests/test_data_collection_client.py | rg -n 'lease|heartbeat|waiting|redact|retry'
```

不要运行采集客户端，不查看输出目录。画出状态迁移，并标注 3 分钟租约、默认 60 秒心跳和 `PROJECT_COLLECTION_NOT_COLLECTABLE_YET` 的 waiting 语义。

### 可选分支练习

```bash
git switch -c course/fa05-collection-state 710807b
```

只补一个纯本地状态机测试，例如 marker 即使伴随退出码 0 也应进入 waiting。

### 回滚

```bash
git diff -- client/Data-Collection/main.py tests/test_data_collection_client.py
git restore --staged -- client/Data-Collection/main.py tests/test_data_collection_client.py
git restore --source=HEAD -- client/Data-Collection/main.py tests/test_data_collection_client.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_data_collection_client.py
git diff --check
```

验收覆盖领取、续租、waiting、租约失效、结果重试和错误脱敏，不触发外部采集或数据库同步。

## FA06 查询导出与AI

### 目标

区分在线查询、同步/异步导出、受权下载和 AI 长任务的执行与安全模型。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:app/enterprise_data_platform/api/routes.py | rg -n '^@router|response_model|export|download|owner|capacity' | sed -n '1,240p'
git show 710807b:app/enterprise_data_platform/ai/routes.py | rg -n '^@router|quota|task|lease|web.search|extract' | sed -n '1,220p'
git show 710807b:app/enterprise_data_platform/ai/task_manager.py | rg -n 'lease|setex|task_ttl|active|lock' | sed -n '1,200p'
git show 710807b:tests/test_export_security.py | rg -n '^def test_'
```

不要生成导出，不调用 AI 或联网搜索。为每个端点记录权限、输入上限、异步状态、归属校验和失败清理。

### 可选分支练习

```bash
git switch -c course/fa06-export-review 710807b
```

选择一个安全边界补测试，例如非 2xx 不落盘或非 owner 不可下载，不扩大 API 表面。

### 回滚

```bash
git diff -- app/enterprise_data_platform/api/routes.py tests/test_export_security.py
git restore --staged -- app/enterprise_data_platform/api/routes.py tests/test_export_security.py
git restore --source=HEAD -- app/enterprise_data_platform/api/routes.py tests/test_export_security.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_export_security.py tests/test_ai_routes.py
git diff --check
```

验收必须证明路径、owner、权限和清理合同未被削弱；AI 测试只使用本地替身。

## FA07 邮件营销

### 目标

理解邮件任务从创建、入队、worker 执行、持久记录到供应商事件回调的闭环。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:app/internet_marketing/routes.py | rg -n 'email/tasks|email/history|events|HMAC|export'
git show 710807b:app/internet_marketing/email_queue.py | rg -n 'worker|lock|status|recovery|orphan|setex|SessionLocal' | sed -n '1,240p'
git show 710807b:app/internet_marketing/email_policy.py | rg -n '^def |window|interval|policy'
git show 710807b:tests/test_internet_marketing_queue_consumer.py | rg -n '^def test_' | sed -n '1,180p'
```

不要查看队列 payload、真实邮箱、邮件内容或历史记录。把状态机分为任务状态、队列状态、投递状态和回调状态。

### 可选分支练习

```bash
git switch -c course/fa07-email-queue 710807b
```

补一个恢复或重复回调测试，优先锁定幂等行为，不改供应商配置。

### 回滚

```bash
git diff -- app/internet_marketing/email_queue.py tests/test_internet_marketing_queue_consumer.py
git restore --staged -- app/internet_marketing/email_queue.py tests/test_internet_marketing_queue_consumer.py
git restore --source=HEAD -- app/internet_marketing/email_queue.py tests/test_internet_marketing_queue_consumer.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_internet_marketing_queue_consumer.py tests/test_internet_marketing_tracking_events.py
git diff --check
```

验收覆盖孤儿状态、重复事件、错误签名、时间窗口和脱敏输出，不发送任何邮件。

## FA08 微信与客户

### 目标

区分服务端微信任务、Windows wxcli 执行、pending/quarantine/ledger 恢复和客户跟进能力。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:client/wxcli/README.md | rg -n 'pending|quarantine|ledger|claim|确认模式|自动模式|客户|回传'
git show 710807b:client/wxcli/src/wxcli/worker.py | rg -n 'pending|claim|result|flush|quarantine'
git show 710807b:client/wxcli/src/wxcli/ledger.py | rg -n '^class |^def |digest|stage'
git show 710807b:app/internet_marketing/routes.py | rg -n 'wechat/tasks|claim-next|result|claim-reset|sync-batch|customer-management'
```

不要读取本机 wxcli 状态文件，也不要操作 PC 微信。确认 pending 保存可重试 payload，quarantine 隔离确定不可重试结果，ledger 只保留执行摘要和 digest。

### 可选分支练习

```bash
git switch -c course/fa08-wxcli-recovery 710807b
```

只在临时目录测试 pending 分类或 ledger 摘要，不调用真实 adapter。

### 回滚

```bash
git diff -- client/wxcli/src/wxcli/worker.py tests/test_wxcli_runtime.py
git restore --staged -- client/wxcli/src/wxcli/worker.py tests/test_wxcli_runtime.py
git restore --source=HEAD -- client/wxcli/src/wxcli/worker.py tests/test_wxcli_runtime.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_wxcli_runtime.py tests/test_internet_marketing_wechat_tasks.py
git diff --check
```

验收输出不得包含手机号、Account-Key、Bearer、claim token 或申请全文；短信、电话营销和手工新增客户仍标为未完成。

## FA09 三类客户端

### 目标

比较通用 `fastapi1` CLI、Data-Collection 与 Windows `wx` 的入口、平台、协议和副作用边界。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:client/README.md | sed -n '1,240p'
git show 710807b:client/fastapi1_cli/README.md | rg -n 'preflight|doctor|request|只限|WebSocket|Bearer'
git show 710807b:client/Data-Collection/README.md | rg -n 'WebSocket|常驻|管理员|Windows|macOS'
git show 710807b:client/wxcli/README.md | rg -n 'Windows|PC 微信|RPA|pending|operator confirmation'
```

建立七列表格：命令入口、Python 下限、支持平台、认证、协议、允许副作用、主要测试。

### 可选分支练习

```bash
git switch -c course/fa09-client-contracts 710807b
```

只修正一处客户端文档或合同测试漂移，不复制另一客户端的协议实现。

### 回滚

```bash
git diff -- client/README.md tests/test_fastapi1_cli_skills.py
git restore --staged -- client/README.md tests/test_fastapi1_cli_skills.py
git restore --source=HEAD -- client/README.md tests/test_fastapi1_cli_skills.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_fastapi1_cli.py tests/test_data_collection_client.py tests/test_wxcli_runtime.py
git diff --check
```

验收说明每个需求为什么属于某一客户端，并确认没有新增第二份相同协议。

## FA10 依赖与部署

### 目标

盘点根服务、通用 CLI、Data-Collection 和 wxcli 的依赖及 Python/平台差异。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:requirements.txt | nl -ba
git show 710807b:requirements-tools.txt | nl -ba
git show 710807b:client/fastapi1_cli/pyproject.toml | rg -n 'requires-python|dependencies|scripts'
git show 710807b:client/wxcli/pyproject.toml | rg -n 'requires-python|dependencies|Windows|scripts'
git show 710807b:client/Data-Collection/requirements.txt | nl -ba
git show 710807b:client/fastapi1_cli/install-local.sh | rg -n 'python|venv|pipx|wrapper|install'
git show 710807b:client/fastapi1_cli/install-local.ps1 | rg -n 'Python|pipx|wrapper|install'
git show 710807b:client/wxcli/install-windows.ps1 | rg -n 'Python|3\.10|Windows|venv|pip|install'
git show 710807b:.github/workflows/harness.yml | rg -n 'python-version|pip install|pytest'
```

不要安装或升级任何包。记录 CLI 的 Python 3.11+、wxcli 的 3.10+ 与 Windows 条件依赖，并把根服务、工具链和采集客户端分开评估。

### 可选分支练习

```bash
git switch -c course/fa10-dependency-audit 710807b
```

只在 `README.md` 补充一张组件级兼容矩阵，并在 `tests/test_documentation_governance.py` 锁定 Python 下限、平台条件、安装入口和回滚版本；不要安装、升级或统一依赖。

### 回滚

```bash
git diff -- README.md tests/test_documentation_governance.py
git restore --staged -- README.md tests/test_documentation_governance.py
git restore --source=HEAD -- README.md tests/test_documentation_governance.py
git status --short
```

### 验收

```bash
safe_pytest -q tests/test_fastapi1_cli.py tests/test_wxcli_runtime.py tests/test_data_collection_client.py
safe_pytest -q tests/test_documentation_governance.py
git diff --check
```

验收包含组件级兼容矩阵、安装入口、目标测试和明确回滚版本。当前 Mac 与单一解释器的测试只验证本地合同，不证明 Windows 或其他 Python 版本兼容；Harness 的 Python 3.13 安装成功也不能替代生产兼容证明。

## FA11 测试与Harness

### 目标

区分业务 pytest/Playwright 与 Codex Harness 合同，并识别当前 GitHub CI 覆盖缺口。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git ls-tree -r --name-only 710807b tests | rg 'test_|\.spec\.ts$|endpoint-manifest'
git show 710807b:.github/workflows/harness.yml | sed -n '1,220p'
git show 710807b:.codex/contract.json | sed -n '1,240p'
git show 710807b:scripts/check_harness_health.py | rg -n '^def check_|contract|hooks|mcp|skills'
git ls-tree -r --name-only 710807b .github/workflows
```

不要读取 E2E 凭据。制作模块到单元、集成、E2E、GitHub CI 的映射，明确唯一 workflow 主要执行 Harness 治理检查。

### 可选分支练习

```bash
git switch -c course/fa11-test-map 710807b
```

只为 Harness 健康检查补一个缺失断言，并在必要时调整 `harness.yml`；不要把依赖生产服务的全量命令塞入 workflow。

### 回滚

```bash
git diff -- .github/workflows/harness.yml tests
git restore --staged -- .github/workflows/harness.yml tests/test_harness_health.py
git restore --source=HEAD -- .github/workflows/harness.yml tests/test_harness_health.py
git status --short
```

确认这两个路径没有他人改动后才能回滚。

### 验收

```bash
safe_python scripts/check_harness_health.py
safe_pytest -q tests/test_harness_health.py tests/test_codex_hooks_config.py tests/test_documentation_governance.py
git diff --check
```

验收报告要分别列出 Harness 通过与业务测试通过，不能相互替代；应用 CI 缺口仍需显式记录。

## FA12 审查Codex改动

### 目标

形成一套先看工作区与规则、再追数据流、最后验证和回滚的 Codex 改动审查流程。

### 观察

```bash
cd "$HOME/Documents/fastapi1"
git status --short
git show 710807b:AGENTS.md | sed -n '1,220p'
git show 710807b:.codex/AGENTS.md | sed -n '1,220p'
git show 710807b:.github/workflows/harness.yml | sed -n '1,180p'
git show 710807b:graphify-out/GRAPH_REPORT.md | rg -n 'God Nodes|most connected|app/internet_marketing/services.py|app/index/project_collection_service.py|client/fastapi1_cli/cli.py'
for file in main.py app/internet_marketing/services.py app/index/project_collection_service.py client/fastapi1_cli/cli.py; do
  printf '%s ' "$file"
  git show "710807b:$file" | wc -l
done
git ls-tree -r --name-only 710807b | rg -i 'alembic|migration|db_setup|workflow'
```

观察结论应包含：多个核心文件巨大且高连接、仓库未见 Alembic、main.py 仍有显式门禁的启动期 schema patch、GitHub CI 主要覆盖 Harness。不要因此提出一次性大重写。

### 可选分支练习

```bash
git switch -c course/fa12-review-drill 710807b
```

以 `README.md` 的一条当前架构说明做审查演练：先和固定提交及源码互证，再在必要时修正文档并更新 `tests/test_documentation_governance.py`。不要扩展到业务重构。

### 回滚

```bash
git diff --stat
git diff -- README.md tests/test_documentation_governance.py
git restore --staged -- README.md tests/test_documentation_governance.py
git restore --source=HEAD -- README.md tests/test_documentation_governance.py
git status --short
```

禁止使用 `git reset --hard` 或覆盖未确认来源的工作区改动。需要保留实验时先提交到本课分支，再用普通 `git revert` 生成可审计回滚。

### 验收

```bash
git diff --check
safe_pytest -q tests/test_documentation_governance.py
```

最终审查报告按严重度列出行为风险、文件与行号、缺失测试和回滚方式；没有发现问题时也要说明剩余测试缺口。
