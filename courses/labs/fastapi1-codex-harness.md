# fastapi1 Codex Harness 实验手册

本手册只观察 `fastapi1@710807b32a2a7af6b48496390d15c728a8afd06b` 的 Git 跟踪材料，快照日期为 2026-07-20。每个单元建议 10–15 分钟。

`<SYNTHETIC_HARNESS_CASE>` 表示完全虚构的 Harness 场景；`<PROJECT_ROOT>`、`<PROJECT_DIR>` 与 `<DATABASE_URL_PRESENT>` 只是角色化占位符，不是机器路径或秘密。课程只检查声明、预期证据与停止条件，不执行 Hook、MCP、environment action、agent、Rules 命令或任何写入，也不读取 `.env`、数据库、日志、用户配置、生产状态和客户数据。

## FH01 fastapi1 Codex Harness

### 1. 用途

建议用时：10–15 分钟。

建立 12 个 Harness 组件的地图，并区分治理指令、只读角色、配置声明、运行入口与命令 guardrail。

### 2. 适用与不适用场景

- 适用：问题仍需在 AGENTS、5 个 agent、config、contract、Hooks、environment、MCP 和 Rules 之间路由。
- 不适用：已经明确知道目标组件，或请求课程实际启动 Hook、MCP、环境 action 或外部服务。

### 3. 输入/输出

- 输入：`<SYNTHETIC_HARNESS_CASE>`、固定提交、候选相对路径和要证明的证据层。
- 输出：一个主组件、相邻依赖、静态可证事实、运行未知与停止条件。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
从 12 个 Harness 组件中选择主单元，并说明它是治理、只读角色、声明还是 guardrail。
只检查固定 Git 结构；不要运行 Hook、MCP、environment action 或 agent。
```

### 5. 边界与风险

Harness 组件不是业务执行器。文件存在只证明声明；加载、连接、调用、结果和业务兼容都需要独立证据。

### 6. 提示词练习

```text
合成问题：有人声称“required MCP 已经健康，因为 contract 中有它”。
选择对应单元，写出声明层能证明什么、仍不能证明什么。
```

### 7. 可观察验收清单

- [ ] 能列出 12 个组件单元。
- [ ] 能区分声明、加载、调用与结果。
- [ ] 只读 agent 没有被描述成修复执行器。
- [ ] 所有运行态证据保持未验证。

## FH02 AGENTS 范围

### 1. 用途

建议用时：10–15 分钟。

理解根 AGENTS 与 `.codex/AGENTS.md` 的作用域、近端覆盖和 Harness 维护禁区。

### 2. 适用与不适用场景

- 适用：需要判断 `.codex/**` 内哪条项目指令生效，或核对 repo-specific 与用户级配置边界。
- 不适用：普通业务目录的实现细节，或试图用 AGENTS 代替 Rules、MCP、Hook 或业务权限。

### 3. 输入/输出

- 输入：固定的根/近端 AGENTS、目标相对路径和一个合成配置变化。
- 输出：适用指令链、冲突解析、允许/禁止配置项和需批准变化。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
静态比较根 AGENTS 与 `.codex/AGENTS.md`，指出目标路径的有效规则。
不要读取用户配置或执行任何配置命令。
```

### 5. 边界与风险

`.codex/AGENTS.md` 只约束 Harness 目录，不会抹去所有根规则。额外 Hook 和写入型 Hook 必须先获明确批准。

### 6. 提示词练习

```text
合成冲突：用户级偏好想写入项目 config，同时提议新增 Stop Hook。
分别说明配置归属、批准门槛和需要同步的合同。
```

### 7. 可观察验收清单

- [ ] 说明根到近端的指令发现顺序。
- [ ] 用户级 provider/auth/profile/sandbox 未进入项目配置。
- [ ] Hook 批准与 contract/test 同步被明确。
- [ ] 没有把 AGENTS 当执行机制。

## FH03 data_security 只读角色

### 1. 用途

建议用时：10–15 分钟。

选择只读数据与安全角色，审查认证授权、SQL/Redis、敏感数据流、导出、日志和外部回调。

### 2. 适用与不适用场景

- 适用：主线程需要一份有范围的数据/安全风险分析，而不是立即实施修复。
- 不适用：要求角色写文件、执行写查询、读取秘密值或替主线程发布修复。

### 3. 输入/输出

- 输入：合成 endpoint、角色、资源、字段名、数据流和只读来源范围。
- 输出：按严重度排列的权限/数据风险、证据路径、未知项和给主线程的建议。

### 4. 最小调用模板

```text
角色选择：data_security
场景：<SYNTHETIC_HARNESS_CASE>
只规划 read-only delegation；秘密只说明存在与风险，不回显值。
不要 spawn agent、查询数据库或修改文件。
```

### 5. 边界与风险

TOML 声明 `read-only`，角色不能实施修复。配置存在也不证明角色已启动或完成审查。

### 6. 提示词练习

```text
合成导出接口包含区域权限、Redis 状态和回调日志。
写出交给 data_security 的只读问题与期望证据。
```

### 7. 可观察验收清单

- [ ] 角色关注面与任务匹配。
- [ ] 输出只含风险和建议，不含修复 diff。
- [ ] secret 使用角色化占位符。
- [ ] 启动与实际审查结果标为未运行。

## FH04 docs_researcher 只读角色

### 1. 用途

建议用时：10–15 分钟。

选择只读文档核验角色，以一手资料核对 FastAPI、Pydantic、SQLAlchemy、Redis、Codex/OpenAI 等行为。

### 2. 适用与不适用场景

- 适用：外部行为版本敏感，且主线程需要官方事实、项目事实与推断分栏。
- 不适用：只有本地调用链问题，或请求角色直接修改代码、决定架构或复制 MCP 凭证。

### 3. 输入/输出

- 输入：合成技术问题、目标版本、候选官方页面和对应项目文件。
- 输出：一手来源、适用版本、项目对照、冲突、不确定性与验证建议。

### 4. 最小调用模板

```text
角色选择：docs_researcher
场景：<SYNTHETIC_HARNESS_CASE>
只规划官方文档核验，并区分官方事实、项目事实和推断。
不要 spawn agent、联网或读取用户级 MCP 配置。
```

### 5. 边界与风险

搜索摘要和社区文章不能替代一手来源；官方通用模式也不能自动覆盖仓库测试与规则。

### 6. 提示词练习

```text
合成问题：某个 Pydantic 行为在目标版本是否成立？
写出 delegation prompt、需要的官方来源和找不到依据时的停止条件。
```

### 7. 可观察验收清单

- [ ] 角色选择理由具体。
- [ ] 来源层级和版本明确。
- [ ] 冲突与未验证项没有被抹平。
- [ ] 角色未被授权实现或修改。

## FH05 explorer 只读角色

### 1. 用途

建议用时：10–15 分钟。

选择只读代码勘探角色，定位请求入口、依赖注入、数据流、定时任务与相关测试。

### 2. 适用与不适用场景

- 适用：主线程需要快速建立本地代码地图和精确路径。
- 不适用：要求角色修改文件、运行改写状态的命令、批准架构或替主线程实现。

### 3. 输入/输出

- 输入：合成请求、搜索范围、AGENTS/图谱线索和目标调用链。
- 输出：入口、相对路径、依赖/调用边、数据对象、测试与待确认问题。

### 4. 最小调用模板

```text
角色选择：explorer
场景：<SYNTHETIC_HARNESS_CASE>
只规划源码勘探，从 AGENTS、图谱线索、入口和测试开始。
不要 spawn agent、修改文件或运行状态写命令。
```

### 5. 边界与风险

角色描述是职责，不是本次勘探结果；具体路径与调用边必须来自源码证据。

### 6. 提示词练习

```text
合成需求：追踪一个 API 请求到服务、数据库与定时任务。
写出 explorer 的输入范围和 handoff 字段。
```

### 7. 可观察验收清单

- [ ] 输出含精确相对路径和调用边。
- [ ] 事实与待决问题分开。
- [ ] 没有实现或架构批准。
- [ ] 配置声明与任务结果分层。

## FH06 fastapi_api 只读角色

### 1. 用途

建议用时：10–15 分钟。

选择只读 FastAPI API 角色，核对路由、Depends、response_model、Pydantic v2、异常与认证合同。

### 2. 适用与不适用场景

- 适用：主线程要确认具体 API 声明与前后端接口一致性。
- 不适用：要求角色新增/修改 route、schema、model、测试，或用真实 token 调运行服务。

### 3. 输入/输出

- 输入：合成 endpoint、main/routes/schema/model 相对路径和相关测试。
- 输出：method/path、依赖、响应、错误、权限、测试覆盖与缺口。

### 4. 最小调用模板

```text
角色选择：fastapi_api
场景：<SYNTHETIC_HARNESS_CASE>
只规划静态 API 合同核对，并分开源码、测试和运行证据。
不要 spawn agent、修改代码或调用服务。
```

### 5. 边界与风险

专业关注点不会扩大 read-only 权限；源码路径存在也不证明服务运行或权限正确。

### 6. 提示词练习

```text
合成接口：一个 JSON route 可能缺少 response_model。
写出需要角色核对的六个合同字段。
```

### 7. 可观察验收清单

- [ ] 路由、依赖、响应、错误与权限均覆盖。
- [ ] 运行请求明确未执行。
- [ ] 发现只写影响和建议测试。
- [ ] 没有修复 diff。

## FH07 reviewer 只读角色

### 1. 用途

建议用时：10–15 分钟。

选择只读审查角色，按严重度检查 correctness、权限、缓存、调度、安全边界和测试缺口。

### 2. 适用与不适用场景

- 适用：主线程已有 diff 或固定审查范围，需要证据化 findings。
- 不适用：要求 reviewer 修改文件、提交修复、批准发布，或把“无发现”当系统无风险证明。

### 3. 输入/输出

- 输入：合成 diff、基线、规格、相关测试和重点风险面。
- 输出：按严重度排序的触发条件、影响、精确路径、最小证据与建议测试。

### 4. 最小调用模板

```text
角色选择：reviewer
场景：<SYNTHETIC_HARNESS_CASE>
只规划 findings-only 审查；无发现时也列范围和未运行检查。
不要 spawn agent、修改文件、提交或合并。
```

### 5. 边界与风险

P1 发现不会自动授权修复。角色只审查可见范围，不能证明所有生产路径无缺陷。

### 6. 提示词练习

```text
合成 diff：缓存键变化但缺少权限测试。
写一个可行动发现和一个因证据不足而不应报告的问题。
```

### 7. 可观察验收清单

- [ ] 发现包含触发、影响、路径和证据。
- [ ] 严重度与风险相称。
- [ ] 无发现结论限定范围。
- [ ] 未实施任何修复。

## FH08 项目 config

### 1. 用途

建议用时：10–15 分钟。

理解 `.codex/config.toml` 的 repo-specific features、禁用插件、MCP 声明、agent 注册与并发参数。

### 2. 适用与不适用场景

- 适用：需要核对项目声明允许什么、禁用什么，以及哪些设置不应进入仓库。
- 不适用：需要证明 MCP 已连接、agent 已运行、插件已卸载或业务动作已完成。

### 3. 输入/输出

- 输入：固定 config 与合成键清单，不包含任何真实值或用户配置。
- 输出：允许/禁止/敏感键分类，以及声明、加载、连接、调用各层未知。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
只读检查 `.codex/config.toml` 的 section 和字段名。
不要读取用户 config、启动 MCP、加载插件或 spawn agent。
```

### 5. 边界与风险

项目 config 不保存 provider、auth、profile、approval、sandbox、telemetry 或 secret。注册和 required 声明不等于运行成功。

### 6. 提示词练习

```text
合成配置评审：同时出现 repo MCP、个人 profile 和一个连接串。
将它们分入项目允许、用户级和禁止持久化三类。
```

### 7. 可观察验收清单

- [ ] features/plugins/MCP/agents 均覆盖。
- [ ] 禁止键与 secrets 没有进入输出。
- [ ] 五个 agent 的 read-only 来源可追溯。
- [ ] 运行状态没有从声明推断。

## FH09 结构化 contract

### 1. 用途

建议用时：10–15 分钟。

理解 `.codex/contract.json` 作为 features、插件、MCP、Hooks、Rules、skills、文档锚点和 graphify policy 的结构化事实源。

### 2. 适用与不适用场景

- 适用：需要判断结构化 Harness 事实是否与 config、Hooks、Rules、skills 或文档消费者一致。
- 不适用：纯措辞、普通业务代码，或要求 contract 启动外部组件。

### 3. 输入/输出

- 输入：固定 contract、相关声明文件、合成结构变化和 consumer 清单。
- 输出：expected/actual/consumer 对照、需同步字段、窄验证与未覆盖项。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
静态比较 contract 与 config/hooks/rules/project skills 的对应字段。
不要修改 contract、运行 consumer 或启动外部组件。
```

### 5. 边界与风险

contract 通过只证明结构化一致性；health 不覆盖 Rules 内容或每个字段，required 也不代表已连接。

### 6. 提示词练习

```text
合成变化：新增一个 Hook event 或修改 required MCP。
列出合同字段、声明来源、consumer 与需批准边界。
```

### 7. 可观察验收清单

- [ ] 结构化变化与 prose 变化分开。
- [ ] consumer 选择与字段匹配。
- [ ] required/allow_extra 含义准确。
- [ ] contract 未被描述为执行器。

## FH10 SessionStart Hooks

### 1. 用途

建议用时：10–15 分钟。

理解项目 SessionStart Hook 的 event、matcher、跨平台 command、脚本输入输出和上下文注入。

### 2. 适用与不适用场景

- 适用：需要核对 Hook 声明、脚本副作用与 contract 是否一致。
- 不适用：需要真实触发会话、依赖 Hook 顺序、扩大权限或新增未经批准的事件。

### 3. 输入/输出

- 输入：固定 `hooks.json`、`session_start.py` 与 contract 的 project Hook 字段。
- 输出：event/matcher/command/timeout、脚本 JSON 形状、静态副作用判断和运行未知。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
只读比较 Hook 声明、脚本和 contract；项目根路径使用 `<PROJECT_ROOT>`。
不要执行脚本、触发会话或记录机器绝对路径。
```

### 5. 边界与风险

Hook 只注入上下文，不替代 Rules、sandbox、approval 或业务权限。多个项目/用户/插件 Hook 可能并发，不得假定顺序。

### 6. 提示词练习

```text
合成审查：确认 startup/resume/clear 与 additionalContext 字段。
写出静态可证事实，以及实际加载和并发仍需的证据。
```

### 7. 可观察验收清单

- [ ] event、matcher、command 和 timeout 均覆盖。
- [ ] 脚本输入输出与副作用准确。
- [ ] 机器路径已替换为占位符。
- [ ] Hook 未执行且未被写成权限机制。

## FH11 environment action

### 1. 用途

建议用时：10–15 分钟。

理解自动生成的本地 environment action 声明、默认 host、reload 与 Redis/开发服务器依赖。

### 2. 适用与不适用场景

- 适用：需要解释本地“运行” action 会尝试启动什么，以及为什么课程不能直接运行。
- 不适用：生产部署、Windows VM、MCP 或任何需要启动进程和占用端口的练习。

### 3. 输入/输出

- 输入：固定 `environment.toml` 和合成依赖状态。
- 输出：action 名称、命令分解、外部依赖、副作用、停止条件与运行未知。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
静态读取 `.codex/environments/environment.toml`，分解 action 与预期进程。
不要启动 Redis、开发服务器、端口检查或修改 autogenerated 文件。
```

### 5. 边界与风险

action 是启动声明，不是服务健康证明。文件标记 autogenerated；课程不执行、编辑或访问本地服务。

### 6. 提示词练习

```text
合成状态：Redis 未知、端口未知、依赖未知。
说明 action 文件能证明的声明，以及运行前仍需的检查。
```

### 7. 可观察验收清单

- [ ] 本地 action 与生产部署分开。
- [ ] Redis、server、端口和依赖列为运行未知。
- [ ] autogenerated 边界保留。
- [ ] 未启动任何进程。

## FH12 MCP 配置

### 1. 用途

建议用时：10–15 分钟。

理解 openaiDeveloperDocs、PostgreSQL wrapper、只读 Redis 与禁用 sqlite 的项目 MCP 基线和秘密边界。

### 2. 适用与不适用场景

- 适用：需要核对 MCP 声明、wrapper 数据流、enabled_tools、disabled 状态或 required 合同。
- 不适用：需要读取 `.env`、启动 wrapper/MCP、连接数据库、调用工具或验证真实数据。

### 3. 输入/输出

- 输入：固定 config、contract、wrapper 源码和合成连接状态。
- 输出：名称、声明、最小权限、秘密流、静态可证事实与运行未知。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
只读核对四个 MCP 的声明和权限；连接串仅写 `<DATABASE_URL_PRESENT>`。
不要读取 `.env`、启动进程、连接服务或调用工具。
```

### 5. 边界与风险

PostgreSQL secret 只在 wrapper 到 restricted 子进程的边界；Redis 只开放 get/list；sqlite 默认禁用。required 不等于健康。

### 6. 提示词练习

```text
合成审查：config 声明存在，但所有运行状态未知。
制作声明、权限、秘密、连接、调用五列表。
```

### 7. 可观察验收清单

- [ ] 四个 MCP 均覆盖。
- [ ] wrapper 数据流不含真实 URL。
- [ ] 只读/禁用边界准确。
- [ ] 连接与执行未从 required 推断。

## FH13 Rules

### 1. 用途

建议用时：10–15 分钟。

理解 `.codex/rules/default.rules` 对常见破坏性命令前缀的 forbidden/prompt guardrail 与 inline match 测试。

### 2. 适用与不适用场景

- 适用：需要解释某类递归删除、破坏性 Git 或 find delete 前缀会如何决策。
- 不适用：需要完整 shell 安全证明、实际运行危险命令，或把 Rules 当业务权限和测试替代。

### 3. 输入/输出

- 输入：固定 Rules blob、合成 token 序列和 contract 的 Rules 路径/验证字段。
- 输出：prefix、decision、match/not_match、覆盖限制和额外安全层。

### 4. 最小调用模板

```text
场景：<SYNTHETIC_HARNESS_CASE>
只读分析合成命令 token 会匹配哪类 rule；项目目录只写 `<PROJECT_DIR>`。
不要执行 execpolicy、危险命令或复制机器绝对路径。
```

### 5. 边界与风险

未匹配不代表安全；Rules 不替代 sandbox、approval、AGENTS、业务权限或测试。源文件中的个人路径必须脱敏。

### 6. 提示词练习

```text
合成命令：一个递归删除前缀和一个未覆盖但仍高风险的命令。
分别说明 decision、匹配原因和还需的安全层。
```

### 7. 可观察验收清单

- [ ] forbidden 与 prompt 类别准确。
- [ ] match/not_match 只作静态证据。
- [ ] 个人绝对路径已脱敏。
- [ ] 没有运行危险命令或夸大覆盖。
