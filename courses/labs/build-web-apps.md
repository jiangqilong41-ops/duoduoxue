# build-web-apps：10–15 分钟技能课程

本手册使用 build-web-apps@0.1.2 的 2026-07-20 本地脱敏快照。所有练习只使用合成材料与只读判断。
本手册中的“输出/成品/链接”均指提示词中应列出的预期结构与验收证据，不实际创建、上传、部署、发送或改变外部状态。

## WB01 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 build-web-apps@0.1.2 的技能地图，知道何时从总览路由到每个独立单元：frontend-app-builder（Build Web Apps:前端应用构建器）；frontend-testing-debugging（Build Web Apps:前端测试调试）；react-best-practices（Build Web Apps:React 最佳实践）；shadcn-best-practices（Build Web Apps:shadcn/ui 组件管理）；stripe-best-practices（Build Web Apps:Stripe 最佳实践）；supabase-best-practices（Build Web Apps:Supabase Postgres 最佳实践）。

### 2. 适用与不适用场景

- 适用：先判断插件覆盖范围、skill 分工、输入输出和安全调用方式。
- 不适用：不要把所有任务都路由到同一个 skill，也不要把插件总览当成执行器。

### 3. 输入/输出

- 输入：manifest、canonical skill 清单、每个 SKILL.md 与相邻 agents/openai.yaml 的非敏感元数据。
- 输出：能为合成场景选出正确入口，解释排除理由，并记录停止条件。

### 4. 最小调用模板

~~~
检查插件 build-web-apps 的技能地图。只输出候选 skill、选择理由、所需输入和停止条件；不要调用工具、安装依赖或改变外部状态。
~~~

### 5. 边界与风险

固定使用 build-web-apps@0.1.2 的 local-sanitized 快照，日期为 2026-07-20。练习不读取凭证、客户数据或运行态秘密，也不自动发送、发布、部署或付费。

### 6. 提示词练习

~~~
合成场景：虚构团队描述一个与 build-web-apps 相关的任务。请列出至多两个候选 skill，说明选择/排除理由；只做路由分析，不执行工具。
~~~

### 7. 可观察验收清单

- [ ] 能说出插件名、版本与 skill 数量（6）。
- [ ] 知道第一课是总览，后续每个 canonical skill 各占一个单元。
- [ ] 调用记录同时包含插件名、slug 和 display name。
- [ ] 输出只含路由、理由和停止条件，没有真实外部副作用。

## WB02 Build Web Apps:前端应用构建器

### 1. 用途

建议用时：10–15 分钟。

从零创建或重设计高质量前端应用、dashboard、游戏、hero section 和视觉驱动 UI。 本单元训练的核心判断是：场景明确落在上述用途时，选择 frontend-app-builder，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：从零创建或重设计高质量前端应用、dashboard、游戏、hero section 和视觉驱动 UI。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：先做足够的图像概念并等待设计接受；持续修正视觉/交互/响应式差异；不默认部署或改动真实站点。

### 3. 输入/输出

- 输入：产品目标、受众、页面范围、品牌/视觉方向、合成素材和响应式要求。
- 输出：先获批的视觉概念，再有浏览器验证的忠实实现。

前置依赖：可用的图像概念/浏览器预览环境；没有真实站点写入权限也可完成路由练习。

### 4. 最小调用模板

~~~
使用插件 build-web-apps，显式调用 $build-web-apps:frontend-app-builder（Build Web Apps:前端应用构建器）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

先做足够的图像概念并等待设计接受；持续修正视觉/交互/响应式差异；不默认部署或改动真实站点。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：从零创建或重设计高质量前端应用、dashboard、游戏、hero section 和视觉驱动 UI。 请先复述输入“产品目标、受众、页面范围、品牌/视觉方向、合成素材和响应式要求”，再说明为何选择 $build-web-apps:frontend-app-builder（Build Web Apps:前端应用构建器）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-web-apps、slug frontend-app-builder 和显示名 Build Web Apps:前端应用构建器。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：产品目标、受众、页面范围、品牌/视觉方向、合成素材和响应式要求。
- [ ] 预期输出明确为：先获批的视觉概念，再有浏览器验证的忠实实现。
- [ ] 能复述边界：先做足够的图像概念并等待设计接受；持续修正视觉/交互/响应式差异；不默认部署或改动真实站点。
- [ ] 全程只使用合成材料和只读判断。
## WB03 Build Web Apps:前端测试调试

### 1. 用途

建议用时：10–15 分钟。

通过本地服务器和浏览器循环测试、调试或定点改进已渲染前端。 本单元训练的核心判断是：场景明确落在上述用途时，选择 frontend-testing-debugging，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：通过本地服务器和浏览器循环测试、调试或定点改进已渲染前端。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：浏览器插件可用时优先使用；否则说明原因再用 Playwright；不把生产环境当实验场。

### 3. 输入/输出

- 输入：本地 dev server、目标用户流程、浏览器可用性、视口和预期行为。
- 输出：复现步骤、控制台/网络证据、截图和最小修复后的验证报告。

前置依赖：本地 dev server；优先 Browser 插件，否则说明原因再使用 Playwright。

### 4. 最小调用模板

~~~
使用插件 build-web-apps，显式调用 $build-web-apps:frontend-testing-debugging（Build Web Apps:前端测试调试）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

浏览器插件可用时优先使用；否则说明原因再用 Playwright；不把生产环境当实验场。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：通过本地服务器和浏览器循环测试、调试或定点改进已渲染前端。 请先复述输入“本地 dev server、目标用户流程、浏览器可用性、视口和预期行为”，再说明为何选择 $build-web-apps:frontend-testing-debugging（Build Web Apps:前端测试调试）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-web-apps、slug frontend-testing-debugging 和显示名 Build Web Apps:前端测试调试。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：本地 dev server、目标用户流程、浏览器可用性、视口和预期行为。
- [ ] 预期输出明确为：复现步骤、控制台/网络证据、截图和最小修复后的验证报告。
- [ ] 能复述边界：浏览器插件可用时优先使用；否则说明原因再用 Playwright；不把生产环境当实验场。
- [ ] 全程只使用合成材料和只读判断。
## WB04 Build Web Apps:React 最佳实践

### 1. 用途

建议用时：10–15 分钟。

按 Vercel React/Next.js 规则优化数据获取、bundle、服务端、重渲染和 JavaScript 性能。 本单元训练的核心判断是：场景明确落在上述用途时，选择 react-best-practices，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：按 Vercel React/Next.js 规则优化数据获取、bundle、服务端、重渲染和 JavaScript 性能。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：仅在 React/Next 场景使用；先读相关 rule 文件；不为了套规则重写无关框架或制造未经测量的优化。

### 3. 输入/输出

- 输入：React/Next 文件、数据获取路径、bundle 症状、渲染热点和目标约束。
- 输出：按影响排序的规则命中、修复建议和必要的验证指标。

前置依赖：React 或 Next.js 代码与对应 rule 文件。

### 4. 最小调用模板

~~~
使用插件 build-web-apps，显式调用 $build-web-apps:react-best-practices（Build Web Apps:React 最佳实践）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

仅在 React/Next 场景使用；先读相关 rule 文件；不为了套规则重写无关框架或制造未经测量的优化。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：按 Vercel React/Next.js 规则优化数据获取、bundle、服务端、重渲染和 JavaScript 性能。 请先复述输入“React/Next 文件、数据获取路径、bundle 症状、渲染热点和目标约束”，再说明为何选择 $build-web-apps:react-best-practices（Build Web Apps:React 最佳实践）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-web-apps、slug react-best-practices 和显示名 Build Web Apps:React 最佳实践。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：React/Next 文件、数据获取路径、bundle 症状、渲染热点和目标约束。
- [ ] 预期输出明确为：按影响排序的规则命中、修复建议和必要的验证指标。
- [ ] 能复述边界：仅在 React/Next 场景使用；先读相关 rule 文件；不为了套规则重写无关框架或制造未经测量的优化。
- [ ] 全程只使用合成材料和只读判断。
## WB05 Build Web Apps:shadcn/ui 组件管理

### 1. 用途

建议用时：10–15 分钟。

用项目包管理器和文档管理 shadcn/ui 组件、注册表、preset 与组合。 本单元训练的核心判断是：场景明确落在上述用途时，选择 shadcn-best-practices，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：用项目包管理器和文档管理 shadcn/ui 组件、注册表、preset 与组合。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：先检查项目上下文和已安装清单；使用正确 runner；未指定 registry 时先询问，不猜并执行。

### 3. 输入/输出

- 输入：components.json、项目上下文、package manager、已安装组件和明确的 registry 目标。
- 输出：文档支撑的搜索/添加/修复方案和可审阅的组件组合。

前置依赖：带 components.json 的项目和正确 package manager；registry 必须由用户指定。

### 4. 最小调用模板

~~~
使用插件 build-web-apps（路径 slug：shadcn-best-practices），显式调用 $build-web-apps:shadcn（Build Web Apps:shadcn/ui 组件管理）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

先检查项目上下文和已安装清单；使用正确 runner；未指定 registry 时先询问，不猜并执行。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：用项目包管理器和文档管理 shadcn/ui 组件、注册表、preset 与组合。 请先复述输入“components.json、项目上下文、package manager、已安装组件和明确的 registry 目标”，再说明为何选择 $build-web-apps:shadcn（路径 slug：shadcn-best-practices；调用名：shadcn；Build Web Apps:shadcn/ui 组件管理）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-web-apps、路径 slug shadcn-best-practices、调用名 shadcn 和显示名 Build Web Apps:shadcn/ui 组件管理。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：components.json、项目上下文、package manager、已安装组件和明确的 registry 目标。
- [ ] 预期输出明确为：文档支撑的搜索/添加/修复方案和可审阅的组件组合。
- [ ] 能复述边界：先检查项目上下文和已安装清单；使用正确 runner；未指定 registry 时先询问，不猜并执行。
- [ ] 全程只使用合成材料和只读判断。
## WB06 Build Web Apps:Stripe 最佳实践

### 1. 用途

建议用时：10–15 分钟。

为一次性付款、Payment Element、Setup Intents、Connect、订阅和 Treasury 选择 Stripe 集成路径。 本单元训练的核心判断是：场景明确落在上述用途时，选择 stripe-best-practices，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：为一次性付款、Payment Element、Setup Intents、Connect、订阅和 Treasury 选择 Stripe 集成路径。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：默认使用最新 API/SDK，除非用户指定；先读相关 reference；课程不使用 live key、不收费、不创建真实账户。

### 3. 输入/输出

- 输入：付款/市场/订阅/财务账户需求、集成界面、API 版本偏好和合规约束。
- 输出：推荐 API、相关官方参考和分阶段集成/迁移计划。

前置依赖：Stripe 文档参考与合成业务需求；不需要 live key。

### 4. 最小调用模板

~~~
使用插件 build-web-apps，显式调用 $build-web-apps:stripe-best-practices（Build Web Apps:Stripe 最佳实践）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

默认使用最新 API/SDK，除非用户指定；先读相关 reference；课程不使用 live key、不收费、不创建真实账户。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：为一次性付款、Payment Element、Setup Intents、Connect、订阅和 Treasury 选择 Stripe 集成路径。 请先复述输入“付款/市场/订阅/财务账户需求、集成界面、API 版本偏好和合规约束”，再说明为何选择 $build-web-apps:stripe-best-practices（Build Web Apps:Stripe 最佳实践）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-web-apps、slug stripe-best-practices 和显示名 Build Web Apps:Stripe 最佳实践。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：付款/市场/订阅/财务账户需求、集成界面、API 版本偏好和合规约束。
- [ ] 预期输出明确为：推荐 API、相关官方参考和分阶段集成/迁移计划。
- [ ] 能复述边界：默认使用最新 API/SDK，除非用户指定；先读相关 reference；课程不使用 live key、不收费、不创建真实账户。
- [ ] 全程只使用合成材料和只读判断。
## WB07 Build Web Apps:Supabase Postgres 最佳实践

### 1. 用途

建议用时：10–15 分钟。

按 Supabase/Postgres 规则优化查询、索引、schema、连接池、RLS、锁和监控。 本单元训练的核心判断是：场景明确落在上述用途时，选择 supabase-best-practices，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：按 Supabase/Postgres 规则优化查询、索引、schema、连接池、RLS、锁和监控。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：先读命中的规则和官方文档；练习只用合成数据库；不直接迁移或修改生产 schema。

### 3. 输入/输出

- 输入：合成 SQL、schema、EXPLAIN 计划、RLS 约束、连接和性能目标。
- 输出：按优先级排序的 SQL/schema 建议、证据和验证查询。

前置依赖：合成 Postgres/Supabase schema 或 SQL 与可读取的 EXPLAIN 计划。

### 4. 最小调用模板

~~~
使用插件 build-web-apps（路径 slug：supabase-best-practices），显式调用 $build-web-apps:supabase-postgres-best-practices（Build Web Apps:Supabase Postgres 最佳实践）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

先读命中的规则和官方文档；练习只用合成数据库；不直接迁移或修改生产 schema。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：按 Supabase/Postgres 规则优化查询、索引、schema、连接池、RLS、锁和监控。 请先复述输入“合成 SQL、schema、EXPLAIN 计划、RLS 约束、连接和性能目标”，再说明为何选择 $build-web-apps:supabase-postgres-best-practices（路径 slug：supabase-best-practices；调用名：supabase-postgres-best-practices；Build Web Apps:Supabase Postgres 最佳实践）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-web-apps、路径 slug supabase-best-practices、调用名 supabase-postgres-best-practices 和显示名 Build Web Apps:Supabase Postgres 最佳实践。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：合成 SQL、schema、EXPLAIN 计划、RLS 约束、连接和性能目标。
- [ ] 预期输出明确为：按优先级排序的 SQL/schema 建议、证据和验证查询。
- [ ] 能复述边界：先读命中的规则和官方文档；练习只用合成数据库；不直接迁移或修改生产 schema。
- [ ] 全程只使用合成材料和只读判断。
