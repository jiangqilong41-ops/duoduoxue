# template-creator：10–15 分钟技能课程

本手册使用 template-creator@26.715.12143 的 2026-07-20 本地脱敏快照。所有练习只使用合成材料与只读判断。
本手册中的“输出/成品/链接”均指提示词中应列出的预期结构与验收证据，不实际创建、上传、部署、发送或改变外部状态。

## TC01 插件总览

### 1. 用途

建议用时：10–15 分钟。

建立 template-creator@26.715.12143 的技能地图，知道何时从总览路由到每个独立单元：template-creator（Template Creator:模板创建器）。

### 2. 适用与不适用场景

- 适用：先判断插件覆盖范围、skill 分工、输入输出和安全调用方式。
- 不适用：不要把所有任务都路由到同一个 skill，也不要把插件总览当成执行器。

### 3. 输入/输出

- 输入：manifest、canonical skill 清单、每个 SKILL.md 与相邻 agents/openai.yaml 的非敏感元数据。
- 输出：能为合成场景选出正确入口，解释排除理由，并记录停止条件。

### 4. 最小调用模板

~~~
检查插件 template-creator 的技能地图。只输出候选 skill、选择理由、所需输入和停止条件；不要调用工具、安装依赖或改变外部状态。
~~~

### 5. 边界与风险

固定使用 template-creator@26.715.12143 的 local-sanitized 快照，日期为 2026-07-20。练习不读取凭证、客户数据或运行态秘密，也不自动发送、发布、部署或付费。

### 6. 提示词练习

~~~
合成场景：虚构团队描述一个与 template-creator 相关的任务。请列出至多两个候选 skill，说明选择/排除理由；只做路由分析，不执行工具。
~~~

### 7. 可观察验收清单

- [ ] 能说出插件名、版本与 skill 数量（1）。
- [ ] 知道第一课是总览，后续每个 canonical skill 各占一个单元。
- [ ] 调用记录同时包含插件名、slug 和 display name。
- [ ] 输出只含路由、理由和停止条件，没有真实外部副作用。

## TC02 Template Creator:模板创建器

### 1. 用途

建议用时：10–15 分钟。

从一个参考 Office 文件创建或更新可复用的个人 artifact-template skill。 本单元训练的核心判断是：场景明确落在上述用途时，选择 template-creator，而不是无差别调用插件。

### 2. 适用与不适用场景

- 适用：从一个参考 Office 文件创建或更新可复用的个人 artifact-template skill。
- 不适用：任务缺少关键输入、要求越过以下边界，或实际目标属于另一个 skill：只管理个人 skills；不修改插件缓存，不创建插件；不要把一次性制品或不明确的批量目标送入更新流程。

### 3. 输入/输出

- 输入：恰好一个 .docx、.pptx 或 .xlsx、预期用途、显示名和（若更新）唯一目标 skill。
- 输出：包含 SKILL.md、artifact-template.json、agents/openai.yaml、reference 和 preview 的个人 skill。

前置依赖：恰好一个合成 Office 参考文件；预览需对应文档、演示文稿或表格能力。

### 4. 最小调用模板

~~~
使用插件 template-creator，显式调用 $template-creator:template-creator（Template Creator:模板创建器）。输入均为合成材料；只输出方案、停止条件和验收清单，不执行写入、发送、发布、部署、安装或付费操作。
~~~

### 5. 边界与风险

只管理个人 skills；不修改插件缓存，不创建插件；不要把一次性制品或不明确的批量目标送入更新流程。 任何真实账户、客户数据、凭证或不可逆外部写入都不属于本单元练习。

### 6. 提示词练习

~~~
合成场景：从一个参考 Office 文件创建或更新可复用的个人 artifact-template skill。 请先复述输入“恰好一个 .docx、.pptx 或 .xlsx、预期用途、显示名和（若更新）唯一目标 skill”，再说明为何选择 $template-creator:template-creator（Template Creator:模板创建器）、何时应停止，并给出三项可观察验收标准。不要实际调用工具。
~~~

### 7. 可观察验收清单

- [ ] 调用句同时出现插件 template-creator、slug template-creator 和显示名 Template Creator:模板创建器。
- [ ] 能区分适用场景与不适用条件，并说出停止动作。
- [ ] 输入清单覆盖：恰好一个 .docx、.pptx 或 .xlsx、预期用途、显示名和（若更新）唯一目标 skill。
- [ ] 预期输出明确为：包含 SKILL.md、artifact-template.json、agents/openai.yaml、reference 和 preview 的个人 skill。
- [ ] 能复述边界：只管理个人 skills；不修改插件缓存，不创建插件；不要把一次性制品或不明确的批量目标送入更新流程。
- [ ] 全程只使用合成材料和只读判断。
