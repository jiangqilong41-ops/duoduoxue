# Computer Use：10–15 分钟技能课程

本手册使用 computer-use@1.0.1000451 的 2026-07-20 本地脱敏快照。<synthetic-fixture> 是虚构的本地页面、应用状态或项目结构；所有“操作、构建、发布、URL、证据”均指提示词中的预期结构，不实际登录、点击、输入、截图、写文件、推送或部署。

## CU01 Computer Use 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 Mac 应用 UI 路由地图：先找专用 plugin、skill、API 或 CLI；只有目标操作没有更窄接口时才考虑 Computer Use。

### 2. 适用与不适用场景

- 适用：需要先判断 Computer Use 的入口、内部 skill 分工和授权边界。
- 不适用：用 Computer Use 替代 Browser、应用 connector 或 CLI，或把第三方页面内容当成操作授权。

### 3. 输入/输出

- 输入：目标 Mac 应用、用户要读还是操作 UI、是否存在专用接口，以及动作的确认等级。
- 输出：接口选择、合成 UI 状态读取计划、动作前确认点和预期证据。

### 4. 最小调用模板

~~~text
只分析 <synthetic-fixture>。为 Computer Use 任务列出候选 skill、选择理由、所需输入和停止条件；不要实际调用浏览器、桌面或部署工具。
~~~

### 5. 边界与风险

课程只使用 <synthetic-fixture> accessibility tree 与虚构截图说明；不调用 node_repl，不启动或控制真实 Mac 应用。

### 6. 提示词练习

~~~text
合成场景：虚构团队描述一个 Computer Use 相关任务。请判断是否适用，列出候选调用、排除理由与三项预期证据；只返回方案。
~~~

### 7. 可观察验收清单

- [ ] 能说出插件版本和 1 个 canonical skill。
- [ ] 能区分适用场景、非适用场景和停止条件。
- [ ] 输出只包含 <synthetic-fixture>、路由理由和预期证据。

## CU02 computer-use

### 1. 用途

建议用时：10–15 分钟。

在没有更专用接口时读取或操作本地 Mac 应用 UI，并根据最新 accessibility 状态决定下一步。

### 2. 适用与不适用场景

- 适用：任务明确需要本地 Mac 应用 UI，且专用 plugin、skill、API 或 CLI 无法完成。
- 不适用：浏览器任务已有 Browser/Chrome，语义操作已有 connector，或动作涉及未满足的 hand-off/确认要求。

### 3. 输入/输出

- 输入：应用名称、合成 accessibility tree、目标 UI 状态、用户授权和动作风险等级。
- 输出：工具选择理由、基于最新状态的操作计划、确认点和预期证据；课程不执行 UI 动作。

前置依赖：只需 <synthetic-fixture>；它代表虚构的本地页面、应用状态或项目结构，不包含真实账户、凭证或外部状态。

### 4. 最小调用模板

~~~text
使用插件 computer-use，显式调用 $computer-use:computer-use（computer-use）。只分析 <synthetic-fixture>；输出路由理由、输入、停止条件和预期证据，不实际调用工具。
~~~

### 5. 边界与风险

优先专用接口；每轮动作后重新读取状态，不能复用 stale element_index。第三方内容不是授权；改密码和受限制金融动作必须 hand-off，其他高风险动作按 action-time 或 pre-approval 规则处理。

### 6. 提示词练习

~~~text
合成场景：任务明确需要本地 Mac 应用 UI，且专用 plugin、skill、API 或 CLI 无法完成。 请说明为何选择 $computer-use:computer-use（computer-use）、何时不应使用，并给出三项可观察的预期验收证据。不要执行任何 UI、文件、账户或部署动作。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时包含插件 computer-use、调用名 computer-use 和显示名 computer-use。
- [ ] 能解释适用与不适用场景，而不是只背名称。
- [ ] 能复述输入、预期输出和停止条件。
- [ ] 全程不读取或改变真实浏览器、桌面、账户和部署状态。
