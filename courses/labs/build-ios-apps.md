# build-ios-apps：10–15 分钟技能课程

本手册使用 build-ios-apps@0.1.2 的 2026-07-20 本地脱敏快照。所有练习只使用合成材料与只读判断。
本手册中的“输出/成品/链接”均指提示词中应列出的预期结构与验收证据，不实际创建、上传、部署、发送或改变外部状态。

## IO01 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 build-ios-apps@0.1.2 的技能地图，知道何时从总览路由到每个独立单元：ios-app-intents（Build iOS Apps:App Intents 集成）；ios-debugger-agent（Build iOS Apps:模拟器调试）；ios-ettrace-performance（Build iOS Apps:ETTrace 性能分析）；ios-memgraph-leaks（Build iOS Apps:Memgraph 泄漏分析）；ios-simulator-browser（Build iOS Apps:模拟器浏览器）；swiftui-liquid-glass（Build iOS Apps:SwiftUI 液态玻璃）；swiftui-performance-audit（Build iOS Apps:SwiftUI 性能审计）；swiftui-ui-patterns（Build iOS Apps:SwiftUI 界面模式）；swiftui-view-refactor（Build iOS Apps:SwiftUI 视图重构）。

### 2. 适用与不适用场景

- 适用：先判断插件覆盖范围、skill 分工、输入输出和安全调用方式。
- 不适用：不要把所有任务都路由到同一个 skill，也不要把插件总览当成执行器。

### 3. 输入/输出

- 输入：manifest、canonical skill 清单、每个 SKILL.md 与相邻 agents/openai.yaml 的非敏感元数据。
- 输出：能为合成场景选出正确入口，解释排除理由，并记录停止条件。

### 4. 最小调用模板

~~~
检查插件 build-ios-apps 的技能地图。只输出候选 skill、选择理由、所需输入和停止条件；不要调用工具、安装依赖或改变外部状态。
~~~

### 5. 边界与风险

固定使用 build-ios-apps@0.1.2 的 local-sanitized 快照，日期为 2026-07-20。练习不读取凭证、客户数据或运行态秘密，也不自动发送、发布、部署或付费。

### 6. 提示词练习

~~~
合成场景：虚构团队描述一个与 build-ios-apps 相关的任务。请列出至多两个候选 skill，说明选择/排除理由；只做路由分析，不执行工具。
~~~

### 7. 可观察验收清单

- [ ] 能说出插件名、版本与 skill 数量（9）。
- [ ] 知道第一课是总览，后续每个 canonical skill 各占一个单元。
- [ ] 调用记录同时包含插件名、slug 和 display name。
- [ ] 输出只含路由、理由和停止条件，没有真实外部副作用。

## IO02 Build iOS Apps:App Intents 集成

### 1. 用途

建议用时：10–15 分钟。

为 Shortcuts、Siri、Spotlight、widgets 或 controls 暴露最小有用的 App Intents、entities 与 App Shortcuts。 本单元训练的核心判断是：场景明确落在上述用途时，选择 ios-app-intents，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：为 Shortcuts、Siri、Spotlight、widgets 或 controls 暴露最小有用的 App Intents、entities 与 App Shortcuts。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：从动词和对象开始，保持最小接口；核对 iOS 可用性和失败 handoff，不凭空暴露全部内部模型。

### 3. 输入/输出

- 输入：用户真正需要的动作和对象、目标系统入口、参数、完成后是否打开 App。
- 输出：窄而可发现的 intent/entity 表面、深链或清晰的运行时 handoff 设计。

前置依赖：Xcode/iOS SDK 与目标部署版本信息；仅设计题可不运行项目。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:ios-app-intents（Build iOS Apps:App Intents 集成）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

从动词和对象开始，保持最小接口；核对 iOS 可用性和失败 handoff，不凭空暴露全部内部模型。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：为 Shortcuts、Siri、Spotlight、widgets 或 controls 暴露最小有用的 App Intents、entities 与 App Shortcuts。 请先复述输入“用户真正需要的动作和对象、目标系统入口、参数、完成后是否打开 App”，再说明为何选择 $build-ios-apps:ios-app-intents（Build iOS Apps:App Intents 集成）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug ios-app-intents 和显示名 Build iOS Apps:App Intents 集成。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：用户真正需要的动作和对象、目标系统入口、参数、完成后是否打开 App。
- [ ] 预期输出明确为：窄而可发现的 intent/entity 表面、深链或清晰的运行时 handoff 设计。
- [ ] 能复述边界：从动词和对象开始，保持最小接口；核对 iOS 可用性和失败 handoff，不凭空暴露全部内部模型。
- [ ] 全程只使用合成材料和只读判断。
## IO03 Build iOS Apps:模拟器调试

### 1. 用途

建议用时：10–15 分钟。

用 XcodeBuildMCP 在已启动的 iOS Simulator 上构建、运行、交互和诊断应用。 本单元训练的核心判断是：场景明确落在上述用途时，选择 ios-debugger-agent，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：用 XcodeBuildMCP 在已启动的 iOS Simulator 上构建、运行、交互和诊断应用。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：先发现 Booted simulator；没有启动设备就请求用户启动，不自动启动；只在明确请求时构建或安装。

### 3. 输入/输出

- 输入：项目或 workspace、scheme、已启动模拟器、复现步骤、需要观察的 UI/日志。
- 输出：可复现的 build/run 结果、UI 检查、日志和根因线索。

前置依赖：XcodeBuildMCP 与一个已启动的 Simulator；没有 Booted 设备时先请求用户启动。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:ios-debugger-agent（Build iOS Apps:模拟器调试）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

先发现 Booted simulator；没有启动设备就请求用户启动，不自动启动；只在明确请求时构建或安装。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：用 XcodeBuildMCP 在已启动的 iOS Simulator 上构建、运行、交互和诊断应用。 请先复述输入“项目或 workspace、scheme、已启动模拟器、复现步骤、需要观察的 UI/日志”，再说明为何选择 $build-ios-apps:ios-debugger-agent（Build iOS Apps:模拟器调试）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug ios-debugger-agent 和显示名 Build iOS Apps:模拟器调试。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：项目或 workspace、scheme、已启动模拟器、复现步骤、需要观察的 UI/日志。
- [ ] 预期输出明确为：可复现的 build/run 结果、UI 检查、日志和根因线索。
- [ ] 能复述边界：先发现 Booted simulator；没有启动设备就请求用户启动，不自动启动；只在明确请求时构建或安装。
- [ ] 全程只使用合成材料和只读判断。
## IO04 Build iOS Apps:ETTrace 性能分析

### 1. 用途

建议用时：10–15 分钟。

捕获并解释聚焦且有符号化的 iOS Simulator ETTrace，用于启动或运行延迟和 CPU 热点分析。 本单元训练的核心判断是：场景明确落在上述用途时，选择 ios-ettrace-performance，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：捕获并解释聚焦且有符号化的 iOS Simulator ETTrace，用于启动或运行延迟和 CPU 热点分析。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：只采集一个聚焦流程；先满足符号化门槛，临时链接后清理；不要把未符号化猜测当作结论。

### 3. 输入/输出

- 输入：目标 simulator app、一个明确的开始/结束流程、匹配 UUID 的 dSYM 和性能假设。
- 输出：一份 ETTrace、符号化栈、热点解释和可复现的下一步。

前置依赖：ETTrace 工具链、目标 simulator app 与 UUID 匹配的 dSYM。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:ios-ettrace-performance（Build iOS Apps:ETTrace 性能分析）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

只采集一个聚焦流程；先满足符号化门槛，临时链接后清理；不要把未符号化猜测当作结论。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：捕获并解释聚焦且有符号化的 iOS Simulator ETTrace，用于启动或运行延迟和 CPU 热点分析。 请先复述输入“目标 simulator app、一个明确的开始/结束流程、匹配 UUID 的 dSYM 和性能假设”，再说明为何选择 $build-ios-apps:ios-ettrace-performance（Build iOS Apps:ETTrace 性能分析）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug ios-ettrace-performance 和显示名 Build iOS Apps:ETTrace 性能分析。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：目标 simulator app、一个明确的开始/结束流程、匹配 UUID 的 dSYM 和性能假设。
- [ ] 预期输出明确为：一份 ETTrace、符号化栈、热点解释和可复现的下一步。
- [ ] 能复述边界：只采集一个聚焦流程；先满足符号化门槛，临时链接后清理；不要把未符号化猜测当作结论。
- [ ] 全程只使用合成材料和只读判断。
## IO05 Build iOS Apps:Memgraph 泄漏分析

### 1. 用途

建议用时：10–15 分钟。

从运行中的 simulator 进程或现有 .memgraph 证明泄漏、retain cycle 或内存增长。 本单元训练的核心判断是：场景明确落在上述用途时，选择 ios-memgraph-leaks，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：从运行中的 simulator 进程或现有 .memgraph 证明泄漏、retain cycle 或内存增长。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：区分 app-owned 与系统对象；同一流程复测前后；不把内存暂时增长直接宣布为泄漏。

### 3. 输入/输出

- 输入：目标进程或 memgraph、应释放对象的操作流、前后对照条件。
- 输出：按类型分组的 leak 证据、ownership 线索、最小修复与同流程复测计划。

前置依赖：运行中的 simulator 进程或现有 .memgraph，以及对应泄漏分析工具。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:ios-memgraph-leaks（Build iOS Apps:Memgraph 泄漏分析）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

区分 app-owned 与系统对象；同一流程复测前后；不把内存暂时增长直接宣布为泄漏。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：从运行中的 simulator 进程或现有 .memgraph 证明泄漏、retain cycle 或内存增长。 请先复述输入“目标进程或 memgraph、应释放对象的操作流、前后对照条件”，再说明为何选择 $build-ios-apps:ios-memgraph-leaks（Build iOS Apps:Memgraph 泄漏分析）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug ios-memgraph-leaks 和显示名 Build iOS Apps:Memgraph 泄漏分析。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：目标进程或 memgraph、应释放对象的操作流、前后对照条件。
- [ ] 预期输出明确为：按类型分组的 leak 证据、ownership 线索、最小修复与同流程复测计划。
- [ ] 能复述边界：区分 app-owned 与系统对象；同一流程复测前后；不把内存暂时增长直接宣布为泄漏。
- [ ] 全程只使用合成材料和只读判断。
## IO06 Build iOS Apps:模拟器浏览器

### 1. 用途

建议用时：10–15 分钟。

把 iOS Simulator 镜像到 Codex 浏览器，并从可导入 Swift package 渲染可热重载的 SwiftUI preview。 本单元训练的核心判断是：场景明确落在上述用途时，选择 ios-simulator-browser，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：把 iOS Simulator 镜像到 Codex 浏览器，并从可导入 Swift package 渲染可热重载的 SwiftUI preview。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：必须使用明确 UDID，不猜设备；启动前清理同设备 stale helper，退出时清理；仅覆盖支持的 preview/package 边界。

### 3. 输入/输出

- 输入：已有流程提供的明确 simulator UDID、serve-sim 环境、可导入 package 和预览目标。
- 输出：浏览器可见的 simulator/SwiftUI preview 与可核验截图或状态。

前置依赖：明确 simulator UDID、serve-sim 和可导入 Swift package。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:ios-simulator-browser（Build iOS Apps:模拟器浏览器）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

必须使用明确 UDID，不猜设备；启动前清理同设备 stale helper，退出时清理；仅覆盖支持的 preview/package 边界。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：把 iOS Simulator 镜像到 Codex 浏览器，并从可导入 Swift package 渲染可热重载的 SwiftUI preview。 请先复述输入“已有流程提供的明确 simulator UDID、serve-sim 环境、可导入 package 和预览目标”，再说明为何选择 $build-ios-apps:ios-simulator-browser（Build iOS Apps:模拟器浏览器）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug ios-simulator-browser 和显示名 Build iOS Apps:模拟器浏览器。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：已有流程提供的明确 simulator UDID、serve-sim 环境、可导入 package 和预览目标。
- [ ] 预期输出明确为：浏览器可见的 simulator/SwiftUI preview 与可核验截图或状态。
- [ ] 能复述边界：必须使用明确 UDID，不猜设备；启动前清理同设备 stale helper，退出时清理；仅覆盖支持的 preview/package 边界。
- [ ] 全程只使用合成材料和只读判断。
## IO07 Build iOS Apps:SwiftUI 液态玻璃

### 1. 用途

建议用时：10–15 分钟。

实现或审查 iOS 26+ SwiftUI Liquid Glass，检查 API、性能和设计适配。 本单元训练的核心判断是：场景明确落在上述用途时，选择 swiftui-liquid-glass，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：实现或审查 iOS 26+ SwiftUI Liquid Glass，检查 API、性能和设计适配。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：核对 iOS 26+ availability、modifier 顺序和容器位置；不为装饰而滥用玻璃，也不牺牲交互和性能。

### 3. 输入/输出

- 输入：目标视图、部署目标、玻璃表面/按钮/卡片、交互和 fallback 要求。
- 输出：基于原生 glassEffect/容器/按钮样式的实现或审查清单，并有可用性 fallback。

前置依赖：iOS 26 SDK/部署目标信息；较低版本需提供 fallback 约束。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:swiftui-liquid-glass（Build iOS Apps:SwiftUI 液态玻璃）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

核对 iOS 26+ availability、modifier 顺序和容器位置；不为装饰而滥用玻璃，也不牺牲交互和性能。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：实现或审查 iOS 26+ SwiftUI Liquid Glass，检查 API、性能和设计适配。 请先复述输入“目标视图、部署目标、玻璃表面/按钮/卡片、交互和 fallback 要求”，再说明为何选择 $build-ios-apps:swiftui-liquid-glass（Build iOS Apps:SwiftUI 液态玻璃）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug swiftui-liquid-glass 和显示名 Build iOS Apps:SwiftUI 液态玻璃。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：目标视图、部署目标、玻璃表面/按钮/卡片、交互和 fallback 要求。
- [ ] 预期输出明确为：基于原生 glassEffect/容器/按钮样式的实现或审查清单，并有可用性 fallback。
- [ ] 能复述边界：核对 iOS 26+ availability、modifier 顺序和容器位置；不为装饰而滥用玻璃，也不牺牲交互和性能。
- [ ] 全程只使用合成材料和只读判断。
## IO08 Build iOS Apps:SwiftUI 性能审计

### 1. 用途

建议用时：10–15 分钟。

先从代码审计 SwiftUI 慢渲染、卡顿、昂贵更新、CPU 或内存症状，再决定是否需要 profile。 本单元训练的核心判断是：场景明确落在上述用途时，选择 swiftui-performance-audit，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：先从代码审计 SwiftUI 慢渲染、卡顿、昂贵更新、CPU 或内存症状，再决定是否需要 profile。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：有代码先 code-first；证据不足时索取最小切片；不凭单一猜测改架构或宣称已验证。

### 3. 输入/输出

- 输入：目标 view、数据流、复现步骤、部署目标和已有运行证据。
- 输出：症状分类、证据链、可能原因、最小修复和必要时的 profiling intake。

前置依赖：目标 SwiftUI 代码；只有需要运行证据时才准备 profiler。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:swiftui-performance-audit（Build iOS Apps:SwiftUI 性能审计）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

有代码先 code-first；证据不足时索取最小切片；不凭单一猜测改架构或宣称已验证。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：先从代码审计 SwiftUI 慢渲染、卡顿、昂贵更新、CPU 或内存症状，再决定是否需要 profile。 请先复述输入“目标 view、数据流、复现步骤、部署目标和已有运行证据”，再说明为何选择 $build-ios-apps:swiftui-performance-audit（Build iOS Apps:SwiftUI 性能审计）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug swiftui-performance-audit 和显示名 Build iOS Apps:SwiftUI 性能审计。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：目标 view、数据流、复现步骤、部署目标和已有运行证据。
- [ ] 预期输出明确为：症状分类、证据链、可能原因、最小修复和必要时的 profiling intake。
- [ ] 能复述边界：有代码先 code-first；证据不足时索取最小切片；不凭单一猜测改架构或宣称已验证。
- [ ] 全程只使用合成材料和只读判断。
## IO09 Build iOS Apps:SwiftUI 界面模式

### 1. 用途

建议用时：10–15 分钟。

用 SwiftUI 组件模式设计或重构导航、状态、布局、控件和屏幕组合。 本单元训练的核心判断是：场景明确落在上述用途时，选择 swiftui-ui-patterns，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：用 SwiftUI 组件模式设计或重构导航、状态、布局、控件和屏幕组合。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：优先 SwiftUI 原生状态与环境注入；按需读组件参考；不为每个画面引入不必要的 view model。

### 3. 输入/输出

- 输入：屏幕交互模型、附近示例、状态所有权、依赖注入和可访问性要求。
- 输出：符合本地约定的视图、导航、状态和组件组合。

前置依赖：SwiftUI 项目或可读的合成视图片段。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:swiftui-ui-patterns（Build iOS Apps:SwiftUI 界面模式）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

优先 SwiftUI 原生状态与环境注入；按需读组件参考；不为每个画面引入不必要的 view model。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：用 SwiftUI 组件模式设计或重构导航、状态、布局、控件和屏幕组合。 请先复述输入“屏幕交互模型、附近示例、状态所有权、依赖注入和可访问性要求”，再说明为何选择 $build-ios-apps:swiftui-ui-patterns（Build iOS Apps:SwiftUI 界面模式）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug swiftui-ui-patterns 和显示名 Build iOS Apps:SwiftUI 界面模式。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：屏幕交互模型、附近示例、状态所有权、依赖注入和可访问性要求。
- [ ] 预期输出明确为：符合本地约定的视图、导航、状态和组件组合。
- [ ] 能复述边界：优先 SwiftUI 原生状态与环境注入；按需读组件参考；不为每个画面引入不必要的 view model。
- [ ] 全程只使用合成材料和只读判断。
## IO10 Build iOS Apps:SwiftUI 视图重构

### 1. 用途

建议用时：10–15 分钟。

把大型 SwiftUI view 拆成稳定、可测试的显式子视图，收紧数据流和 Observation ownership。 本单元训练的核心判断是：场景明确落在上述用途时，选择 swiftui-view-refactor，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：把大型 SwiftUI view 拆成稳定、可测试的显式子视图，收紧数据流和 Observation ownership。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：默认 MV 而非新增 MVVM；避免顶层条件替换 view tree；只有已有或明确要求时才保留 view model。

### 3. 输入/输出

- 输入：现有 view 文件、局部约定、数据流、动作/副作用和测试目标。
- 输出：稳定 view tree、专用子视图、移出 body 的动作与清晰的状态归属。

前置依赖：待重构的 SwiftUI view 文件和可复现的测试目标。

### 4. 最小调用模板

~~~
使用插件 build-ios-apps，显式调用 $build-ios-apps:swiftui-view-refactor（Build iOS Apps:SwiftUI 视图重构）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

默认 MV 而非新增 MVVM；避免顶层条件替换 view tree；只有已有或明确要求时才保留 view model。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：把大型 SwiftUI view 拆成稳定、可测试的显式子视图，收紧数据流和 Observation ownership。 请先复述输入“现有 view 文件、局部约定、数据流、动作/副作用和测试目标”，再说明为何选择 $build-ios-apps:swiftui-view-refactor（Build iOS Apps:SwiftUI 视图重构）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 build-ios-apps、slug swiftui-view-refactor 和显示名 Build iOS Apps:SwiftUI 视图重构。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：现有 view 文件、局部约定、数据流、动作/副作用和测试目标。
- [ ] 预期输出明确为：稳定 view tree、专用子视图、移出 body 的动作与清晰的状态归属。
- [ ] 能复述边界：默认 MV 而非新增 MVVM；避免顶层条件替换 view tree；只有已有或明确要求时才保留 view model。
- [ ] 全程只使用合成材料和只读判断。
