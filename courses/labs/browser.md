# Browser：10–15 分钟技能课程

本手册使用 browser@26.715.52143 的 2026-07-20 本地脱敏快照。<synthetic-fixture> 是虚构的本地页面、应用状态或项目结构；所有“操作、构建、发布、URL、证据”均指提示词中的预期结构，不实际登录、点击、输入、截图、写文件、推送或部署。

## BR01 Browser 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 in-app Browser 的路由地图：显式浏览器/UI 意图使用 Browser；链接资源的语义操作先找专用 connector、API 或 CLI。

### 2. 适用与不适用场景

- 适用：需要先判断 Browser 的入口、内部 skill 分工和授权边界。
- 不适用：把普通 URL 当成浏览器指令，或用 Browser 代替能完成语义操作的专用接口。

### 3. 输入/输出

- 输入：用户是否明确指定 in-app Browser、目标 URL 或本地页面，以及要观察的可见/UI 状态。
- 输出：Browser 与非浏览器接口的选择理由、所需输入、停止条件和预期可见证据。

### 4. 最小调用模板

~~~text
只分析 <synthetic-fixture>。为 Browser 任务列出候选 skill、选择理由、所需输入和停止条件；不要实际调用浏览器、桌面或部署工具。
~~~

### 5. 边界与风险

课程只分析 <synthetic-fixture> 本地页面；不启动浏览器、不读取登录态，也不点击、输入或截图真实页面。

### 6. 提示词练习

~~~text
合成场景：虚构团队描述一个 Browser 相关任务。请判断是否适用，列出候选调用、排除理由与三项预期证据；只返回方案。
~~~

### 7. 可观察验收清单

- [ ] 能说出插件版本和 1 个 canonical skill。
- [ ] 能区分适用场景、非适用场景和停止条件。
- [ ] 输出只包含 <synthetic-fixture>、路由理由和预期证据。

## BR02 Browser

### 1. 用途

建议用时：10–15 分钟。

控制 in-app Browser 打开、导航、检查可见或可交互页面状态，并测试本地 Web 页面。

### 2. 适用与不适用场景

- 适用：用户明确指定 in-app Browser，或任务需要观察/操作本地页面的可见 UI。
- 不适用：对链接文档、日历或业务记录做语义操作且已有 connector/API/CLI；或者只因上下文中有 URL 就启动浏览器。

### 3. 输入/输出

- 输入：明确的浏览器选择或目标 URL、要检查的 UI 流程、预期可见状态与停止条件。
- 输出：浏览器选择理由、只读/本地测试步骤和预期页面证据；课程不产生真实浏览器结果。

前置依赖：只需 <synthetic-fixture>；它代表虚构的本地页面、应用状态或项目结构，不包含真实账户、凭证或外部状态。

### 4. 最小调用模板

~~~text
使用插件 browser，显式调用 $browser:control-in-app-browser（Browser）。只分析 <synthetic-fixture>；输出路由理由、输入、停止条件和预期证据，不实际调用工具。
~~~

### 5. 边界与风险

先判断操作表面；不得检查 cookies、local storage、profiles、passwords 或 session stores。显式指定的 in-app Browser 不可用时应直接说明，不得擅自换用 Chrome、Computer Use 或 Playwright。

### 6. 提示词练习

~~~text
合成场景：用户明确指定 in-app Browser，或任务需要观察/操作本地页面的可见 UI。 请说明为何选择 $browser:control-in-app-browser（Browser）、何时不应使用，并给出三项可观察的预期验收证据。不要执行任何 UI、文件、账户或部署动作。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时包含插件 browser、调用名 control-in-app-browser 和显示名 Browser。
- [ ] 能解释适用与不适用场景，而不是只背名称。
- [ ] 能复述输入、预期输出和停止条件。
- [ ] 全程不读取或改变真实浏览器、桌面、账户和部署状态。
