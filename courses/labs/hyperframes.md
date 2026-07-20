# hyperframes：10–15 分钟技能课程

本手册使用 `hyperframes@0.1.2` 的 `2026-07-20` 本地脱敏快照。所有练习只使用合成材料与只读判断。
本手册中的“输出/成品/链接”均指提示词中应列出的预期结构与验收证据，不实际创建、上传、部署、发送或改变外部状态。


## HF01 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 `hyperframes@0.1.2` 的技能地图：把 HTML 视频需求路由到合成创作、GSAP 动画、CLI、组件库或网站转视频流程。

### 2. 适用与不适用场景

- 适用：需要先判断插件覆盖范围、skill 分工和安全调用方式。
- 不适用：不要把创作规则、命令行操作、组件接线与网站捕获误当成同一个技能。

### 3. 输入/输出

- 输入：插件 manifest、canonical skill 清单、相邻 `agents/openai.yaml` 的显示名与调用策略。
- 输出：能解释总览课与 5 个 skill 单元的对应关系，并为合成场景选出正确入口。

### 4. 最小调用模板

```text
检查插件 hyperframes 的技能地图。只输出候选 skill、选择理由、所需输入和停止条件；不要调用工具、安装依赖或改变外部状态。
```

### 5. 边界与风险

固定使用 `local-sanitized` 的 `0.1.2` 快照；课程示例不读取凭证、客户数据或运行态秘密，也不自动发送、发布、部署或付费。

### 6. 提示词练习

```text
合成场景：一家虚构团队描述了一个与本插件相关的任务。请列出至多两个候选 skill，说明为什么选择或排除；只做路由分析。
```

### 7. 可观察验收清单

- [ ] 能说出插件名、版本与 skill 数量。
- [ ] 知道第一课是总览，后续每个 canonical skill 各占一个单元。
- [ ] 调用记录同时包含插件名、slug 和 display name。
- [ ] 输出只含路由、理由和停止条件，没有真实外部副作用。

## HF02 HyperFrames:GSAP 动画参考

### 1. 用途

建议用时：10–15 分钟。

在 HyperFrames 合成中编写 GSAP 动画、时间线、缓动和性能优化。本单元训练的核心判断是：场景属于“在 HyperFrames 合成中编写 tween、timeline、缓动、stagger 与性能优化”时选择它。

### 2. 适用与不适用场景

- 适用：在 HyperFrames 合成中编写 tween、timeline、缓动、stagger 与性能优化。
- 不适用：需要初始化、预览、渲染或排查 CLI 环境。

### 3. 输入/输出

- 输入：已存在的 DOM、动画目标、时序、属性与可访问性要求。
- 输出：可注册、可控制且使用 transform 优先的 GSAP 时间线方案。

### 4. 最小调用模板

```text
使用插件 hyperframes，显式调用 $hyperframes:gsap（HyperFrames:GSAP 动画参考）。输入均为合成材料；只输出执行方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
```

### 5. 边界与风险

DOM 存在后再建 tween；避免布局属性并在不用时清理动画。任何真实账户、客户数据、凭证或外部写入都不属于本单元练习。

### 6. 提示词练习

```text
合成场景：在 HyperFrames 合成中编写 tween、timeline、缓动、stagger 与性能优化。请先复述所需输入，再说明为何选择 $hyperframes:gsap、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
```

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 `hyperframes`、slug `gsap` 和显示名 `HyperFrames:GSAP 动画参考`。
- [ ] 能用一句话区分适用场景与“不适用：需要初始化、预览、渲染或排查 CLI 环境”。
- [ ] 输入清单覆盖：已存在的 DOM、动画目标、时序、属性与可访问性要求。
- [ ] 预期输出明确为：可注册、可控制且使用 transform 优先的 GSAP 时间线方案。
- [ ] 明确保留边界：DOM 存在后再建 tween；避免布局属性并在不用时清理动画。
- [ ] 全程只使用合成材料和只读判断。

## HF03 HyperFrames:HyperFrames 视频制作

### 1. 用途

建议用时：10–15 分钟。

创建视频合成、动画、标题卡、字幕、配音和音频响应视觉。本单元训练的核心判断是：场景属于“创作 HTML 视频合成、字幕、配音、转场和音频响应视觉”时选择它。

### 2. 适用与不适用场景

- 适用：创作 HTML 视频合成、字幕、配音、转场和音频响应视觉。
- 不适用：问题仅是 CLI 命令、registry 安装或 GSAP API 查询。

### 3. 输入/输出

- 输入：叙事、画幅、素材、时长、布局、视觉风格与音频。
- 输出：符合 data 属性和 timeline contract、通过 lint/validate/inspect 的合成项目。

前置依赖：可用的 HyperFrames 项目环境；涉及预览或渲染时还需满足 Node.js、Chrome 与 FFmpeg 要求。

### 4. 最小调用模板

```text
使用插件 hyperframes，显式调用 $hyperframes:hyperframes（HyperFrames:HyperFrames 视频制作）。输入均为合成材料；只输出执行方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
```

### 5. 边界与风险

时间线必须同步注册且可确定；多场景必须用转场并保留逐元素入场。任何真实账户、客户数据、凭证或外部写入都不属于本单元练习。

占位符说明：`<HARD-GATE>` 标记视觉身份的强制门槛；在编写任何 composition HTML 前必须先满足该段要求。

### 6. 提示词练习

```text
合成场景：创作 HTML 视频合成、字幕、配音、转场和音频响应视觉。请先复述所需输入，再说明为何选择 $hyperframes:hyperframes、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
```

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 `hyperframes`、slug `hyperframes` 和显示名 `HyperFrames:HyperFrames 视频制作`。
- [ ] 能用一句话区分适用场景与“不适用：问题仅是 CLI 命令、registry 安装或 GSAP API 查询”。
- [ ] 输入清单覆盖：叙事、画幅、素材、时长、布局、视觉风格与音频。
- [ ] 预期输出明确为：符合 data 属性和 timeline contract、通过 lint/validate/inspect 的合成项目。
- [ ] 明确保留边界：时间线必须同步注册且可确定；多场景必须用转场并保留逐元素入场。
- [ ] 全程只使用合成材料和只读判断。

## HF04 HyperFrames:HyperFrames 命令行

### 1. 用途

建议用时：10–15 分钟。

使用 HyperFrames CLI 初始化、检查、预览、渲染、转录和生成语音。本单元训练的核心判断是：场景属于“初始化、lint、inspect、preview、render、转录或诊断 HyperFrames 项目”时选择它。

### 2. 适用与不适用场景

- 适用：初始化、lint、inspect、preview、render、转录或诊断 HyperFrames 项目。
- 不适用：主要任务是设计合成内容或编写动画细节。

### 3. 输入/输出

- 输入：项目目录、所需命令、Node、FFmpeg 与输出质量。
- 输出：CLI 检查结果、Studio 项目 URL 或明确请求后的渲染文件。

前置依赖：可用的 HyperFrames 项目环境；涉及预览或渲染时还需满足 Node.js、Chrome 与 FFmpeg 要求。

### 4. 最小调用模板

```text
使用插件 hyperframes，显式调用 $hyperframes:hyperframes-cli（HyperFrames:HyperFrames 命令行）。输入均为合成材料；只输出执行方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
```

### 5. 边界与风险

先 lint 和 inspect 再 preview/render；交付 Studio URL 而不是把 index.html 当预览。任何真实账户、客户数据、凭证或外部写入都不属于本单元练习。

### 6. 提示词练习

```text
合成场景：初始化、lint、inspect、preview、render、转录或诊断 HyperFrames 项目。请先复述所需输入，再说明为何选择 $hyperframes:hyperframes-cli、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
```

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 `hyperframes`、slug `hyperframes-cli` 和显示名 `HyperFrames:HyperFrames 命令行`。
- [ ] 能用一句话区分适用场景与“不适用：主要任务是设计合成内容或编写动画细节”。
- [ ] 输入清单覆盖：项目目录、所需命令、Node、FFmpeg 与输出质量。
- [ ] 预期输出明确为：CLI 检查结果、Studio 项目 URL 或明确请求后的渲染文件。
- [ ] 明确保留边界：先 lint 和 inspect 再 preview/render；交付 Studio URL 而不是把 index.html 当预览。
- [ ] 全程只使用合成材料和只读判断。

## HF05 HyperFrames:HyperFrames 组件库

### 1. 用途

建议用时：10–15 分钟。

安装并接线 HyperFrames 注册表区块和组件到视频合成项目。本单元训练的核心判断是：场景属于“发现、安装并接线 HyperFrames blocks 或 components”时选择它。

### 2. 适用与不适用场景

- 适用：发现、安装并接线 HyperFrames blocks 或 components。
- 不适用：要使用 example 模板，或不需要复用 registry 项。

### 3. 输入/输出

- 输入：registry item 名称、项目目录、宿主合成和安装输出。
- 输出：正确路径的区块或组件以及匹配宿主的接线片段。

前置依赖：可用的 HyperFrames 项目环境；涉及预览或渲染时还需满足 Node.js、Chrome 与 FFmpeg 要求。

### 4. 最小调用模板

```text
使用插件 hyperframes，显式调用 $hyperframes:hyperframes-registry（HyperFrames:HyperFrames 组件库）。输入均为合成材料；只输出执行方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
```

### 5. 边界与风险

block 用 data-composition-src；component 合并片段，二者不能混用。任何真实账户、客户数据、凭证或外部写入都不属于本单元练习。

### 6. 提示词练习

```text
合成场景：发现、安装并接线 HyperFrames blocks 或 components。请先复述所需输入，再说明为何选择 $hyperframes:hyperframes-registry、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
```

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 `hyperframes`、slug `hyperframes-registry` 和显示名 `HyperFrames:HyperFrames 组件库`。
- [ ] 能用一句话区分适用场景与“不适用：要使用 example 模板，或不需要复用 registry 项”。
- [ ] 输入清单覆盖：registry item 名称、项目目录、宿主合成和安装输出。
- [ ] 预期输出明确为：正确路径的区块或组件以及匹配宿主的接线片段。
- [ ] 明确保留边界：block 用 data-composition-src；component 合并片段，二者不能混用。
- [ ] 全程只使用合成材料和只读判断。

## HF06 HyperFrames:网站转 HyperFrames 视频

### 1. 用途

建议用时：10–15 分钟。

抓取网站内容并制作 HyperFrames 产品展示、导览或推广视频。本单元训练的核心判断是：场景属于“从一个网站 URL 制作产品宣传、导览或社交视频”时选择它。

### 2. 适用与不适用场景

- 适用：从一个网站 URL 制作产品宣传、导览或社交视频。
- 不适用：只是调整现有合成的一个颜色、时长或元素。

### 3. 输入/输出

- 输入：可抓取 URL、目标受众、视频类型、画幅、时长与品牌素材。
- 输出：按七个 gate 生成捕获摘要、DESIGN、SCRIPT、STORYBOARD、配音、合成和 Studio 链接。

前置依赖：可用的 HyperFrames 项目环境；涉及预览或渲染时还需满足 Node.js、Chrome 与 FFmpeg 要求。

### 4. 最小调用模板

```text
使用插件 hyperframes，显式调用 $hyperframes:website-to-hyperframes（HyperFrames:网站转 HyperFrames 视频）。输入均为合成材料；只输出执行方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
```

### 5. 边界与风险

每步产物通过 gate 后才继续；默认先交 Studio URL，MP4 需用户明确要求。任何真实账户、客户数据、凭证或外部写入都不属于本单元练习。

### 6. 提示词练习

```text
合成场景：从一个网站 URL 制作产品宣传、导览或社交视频。请先复述所需输入，再说明为何选择 $hyperframes:website-to-hyperframes、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
```

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 `hyperframes`、slug `website-to-hyperframes` 和显示名 `HyperFrames:网站转 HyperFrames 视频`。
- [ ] 能用一句话区分适用场景与“不适用：只是调整现有合成的一个颜色、时长或元素”。
- [ ] 输入清单覆盖：可抓取 URL、目标受众、视频类型、画幅、时长与品牌素材。
- [ ] 预期输出明确为：按七个 gate 生成捕获摘要、DESIGN、SCRIPT、STORYBOARD、配音、合成和 Studio 链接。
- [ ] 明确保留边界：每步产物通过 gate 后才继续；默认先交 Studio URL，MP4 需用户明确要求。
- [ ] 全程只使用合成材料和只读判断。
