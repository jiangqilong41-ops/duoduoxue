# Sites：10–15 分钟技能课程

本手册使用 sites@0.1.30 的 2026-07-20 本地脱敏快照。<synthetic-fixture> 是虚构的本地页面、应用状态或项目结构；所有“操作、构建、发布、URL、证据”均指提示词中的预期结构，不实际登录、点击、输入、截图、写文件、推送或部署。

## SI01 Sites 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 Sites 路由地图：sites-building 负责构建和验证，sites-hosting 负责发布已验证的精确来源。

### 2. 适用与不适用场景

- 适用：需要先判断 Sites 的入口、内部 skill 分工和授权边界。
- 不适用：跳过构建验证直接托管，或在课程练习中创建项目、保存版本、部署、推送和轮询。

### 3. 输入/输出

- 输入：网站目标、是否已有 .openai/hosting.json、是否要求仅本地、构建状态和期望访问级别。
- 输出：building/hosting 的路由、阶段产物、停止条件和只读验收清单。

### 4. 最小调用模板

~~~text
只分析 <synthetic-fixture>。为 Sites 任务列出候选 skill、选择理由、所需输入和停止条件；不要实际调用浏览器、桌面或部署工具。
~~~

### 5. 边界与风险

课程中的“构建、保存、发布、URL”都指 <synthetic-fixture> 的预期结构；不创建站点、不写凭证、不推送或部署。

### 6. 提示词练习

~~~text
合成场景：虚构团队描述一个 Sites 相关任务。请判断是否适用，列出候选调用、排除理由与三项预期证据；只返回方案。
~~~

### 7. 可观察验收清单

- [ ] 能说出插件版本和 2 个 canonical skill。
- [ ] 能区分适用场景、非适用场景和停止条件。
- [ ] 输出只包含 <synthetic-fixture>、路由理由和预期证据。

## SI02 sites-building

### 1. 用途

建议用时：10–15 分钟。

使用 Sites 构建并验证 landing page、portfolio、dashboard、portal、tracker、hub 或内部工具。

### 2. 适用与不适用场景

- 适用：需要新建/修改 Sites 网站，或项目含 .openai/hosting.json；先完成完整构建和验证。
- 不适用：已有成功构建且目标只是发布；或用户只要求一般 Web 代码而未触发 Sites。

### 3. 输入/输出

- 输入：网站目标、现有项目状态、.openai/hosting.json、能力需求和是否明确 local-only。
- 输出：执行路径、网站结构、构建验证和 hosting handoff 的预期清单；课程不创建文件或部署。

前置依赖：只需 <synthetic-fixture>；它代表虚构的本地页面、应用状态或项目结构，不包含真实账户、凭证或外部状态。

### 4. 最小调用模板

~~~text
使用插件 sites，显式调用 $sites:sites-building（sites-building）。只分析 <synthetic-fixture>；输出路由理由、输入、停止条件和预期证据，不实际调用工具。
~~~

### 5. 边界与风险

只有新站点、空/无项目 workspace、单一路由且不需要 D1、R2、上传、认证、connector 或浏览器 QA 时才走 one-shot fast path，否则走 capability path。用户明确 local-only 时不得转入托管。

### 6. 提示词练习

~~~text
合成场景：需要新建/修改 Sites 网站，或项目含 .openai/hosting.json；先完成完整构建和验证。 请说明为何选择 $sites:sites-building（sites-building）、何时不应使用，并给出三项可观察的预期验收证据。不要执行任何 UI、文件、账户或部署动作。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时包含插件 sites、调用名 sites-building 和显示名 sites-building。
- [ ] 能解释适用与不适用场景，而不是只背名称。
- [ ] 能复述输入、预期输出和停止条件。
- [ ] 全程不读取或改变真实浏览器、桌面、账户和部署状态。

## SI03 sites-hosting

### 1. 用途

建议用时：10–15 分钟。

发布 sites-building 已成功验证的精确来源，并管理 Sites 版本与部署状态。

### 2. 适用与不适用场景

- 适用：已有成功且未变更的 Sites 构建，用户要求托管/发布，或项目含 .openai/hosting.json。
- 不适用：网站仍未构建或验证，来源已经变化，或课程练习只要求发布前检查。

### 3. 输入/输出

- 输入：成功构建、project_id、精确来源、commit_sha、打包产物和目标访问级别。
- 输出：复用/创建站点、保存版本、私有或获批访问级别部署与状态轮询的预期序列；课程不执行。

前置依赖：只需 <synthetic-fixture>；它代表虚构的本地页面、应用状态或项目结构，不包含真实账户、凭证或外部状态。

### 4. 最小调用模板

~~~text
使用插件 sites，显式调用 $sites:sites-hosting（sites-hosting）。只分析 <synthetic-fixture>；输出路由理由、输入、停止条件和预期证据，不实际调用工具。
~~~

### 5. 边界与风险

优先私有部署；若只有 shared/public，必须在部署前获得对应访问级别批准。凭证不得进入 remote URL、Git 配置或课程材料；配额、权限和访问错误是终止条件。

### 6. 提示词练习

~~~text
合成场景：已有成功且未变更的 Sites 构建，用户要求托管/发布，或项目含 .openai/hosting.json。 请说明为何选择 $sites:sites-hosting（sites-hosting）、何时不应使用，并给出三项可观察的预期验收证据。不要执行任何 UI、文件、账户或部署动作。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时包含插件 sites、调用名 sites-hosting 和显示名 sites-hosting。
- [ ] 能解释适用与不适用场景，而不是只背名称。
- [ ] 能复述输入、预期输出和停止条件。
- [ ] 全程不读取或改变真实浏览器、桌面、账户和部署状态。
