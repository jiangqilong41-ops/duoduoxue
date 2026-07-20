# spreadsheets 实验手册

来源快照：`spreadsheets@26.715.12143`（2026-07-20）。所有练习仅使用合成 fixture 和只读判断。
合成 fixture 约定：`<synthetic-fixture>` 是占位符，不是工作簿或 Excel 会话；每节至少替换为“Demo”工作表的 3×3 虚构表格、一个公式要求和一个只读目标范围（如 `A1:C3`）。练习不打开或修改工作簿、不导出文件。
本手册中的“输出/成品/链接”均指提示词中应列出的预期结构与验收证据，不实际创建、上传、部署、发送或改变外部状态。
建议用时：每个单元 10–15 分钟。

## SS01 Spreadsheets 插件总览

### 1. 用途

在独立工作簿与 Microsoft Excel 实时会话之间选择正确执行面。

### 2. 适用与不适用场景

- 适用：用户要创建、编辑、分析或验证 XLSX、XLS、CSV、TSV、Google Sheets 目标文件，或明确控制已打开的 Excel 工作簿。
- 不适用：最终产物是 Word、PDF 或纯聊天分析，且没有电子表格输入或输出。

### 3. 输入/输出

- 输入：工作簿目标、文件或 live Excel 线索、目标 sheet/range、计算和交付要求。
- 输出：Spreadsheets 文件工作流或 Excel Live Control 路由，以及对应验收面。

### 4. 最小调用模板

```text
@spreadsheets
请使用 @spreadsheets（Spreadsheets 插件总览；skill slug: 插件入口）。
任务：基于下方合成材料，在独立工作簿与 Microsoft Excel 实时会话之间选择正确执行面。
材料：<synthetic-fixture>
```

### 5. 边界与风险

通用建表默认走独立文件；只有显式 Excel desktop、已打开 workbook 或 add-in 语境才走 live control，不能静默切换。课程练习不得读取真实客户数据、凭据或生产状态，也不得发送、部署或写入外部系统。

### 6. 提示词练习

```text
@spreadsheets
这是一个完全虚构的文件练习：<synthetic-fixture>。
请先判断是否适用，再输出Spreadsheets 文件工作流或 Excel Live Control 路由，以及对应验收面。
不要在 live 连接失败后擅自改做另一份本地工作簿。
```

### 7. 可观察验收清单

- [ ] 明确写出适用理由：“用户要创建、编辑、分析或验证 XLSX、XLS、CSV、TSV、Google Sheets 目标文件，或明确控制已打开的 Excel 工作簿”。
- [ ] 只使用合成输入，并得到Spreadsheets 文件工作流或 Excel Live Control 路由，以及对应验收面。
- [ ] 检查“通用建表默认走独立文件；只有显式 Excel desktop、已打开 workbook 或 add-in 语境才走 live control，不能静默切换”，没有在 live 连接失败后擅自改做另一份本地工作簿。

## SS02 Spreadsheets:Excel 实时控制

### 1. 用途

经过 Excel、目标 workbook、ChatGPT add-in、登录、工具和注册门槛后，用 connected-document 命令修改并验证活动工作簿。

### 2. 适用与不适用场景

- 适用：用户显式标记 Microsoft Excel，或请求针对已打开、活动、已连接 workbook、选区或 add-in 的后续修改。
- 不适用：用户只说创建电子表格、Excel 文件或 workbook，没有指向 Excel desktop 或 live session。

### 3. 输入/输出

- 输入：明确 workbook 标题、sheet/range、当前选区、请求变更和已注册 live session。
- 输出：连接门槛、只读检查计划、预期变更 diff 及关键值/公式/视觉验收字段（练习不修改工作簿）。
- 前置依赖：真实执行需要 Microsoft Excel、ChatGPT add-in、登录和 connected-document tools；课程不控制应用。

### 4. 最小调用模板

```text
@spreadsheets
请使用 $spreadsheets:excel-live-control（Spreadsheets:Excel 实时控制；skill slug: excel-live-control）。
任务：基于下方合成材料，写出经过 Excel、目标 workbook、ChatGPT add-in、登录、工具和注册门槛后进行只读核对的方案，并列出预期变更 diff；不修改活动工作簿。
材料：<synthetic-fixture>
```

### 5. 边界与风险

Computer Use 只用于设置与焦点，单元格读写必须走连接文档工具；任一设置门槛失败时停下，不能改写其他 workbook 或转本地文件。课程练习不得读取真实客户数据、凭据或生产状态，也不得发送、部署或写入外部系统。

### 6. 提示词练习

```text
$spreadsheets:excel-live-control
这是一个完全虚构的文件练习：<synthetic-fixture>。
请先判断是否适用，再输出连接门槛、只读检查计划、预期变更 diff 及关键值/公式/视觉验收字段；不要向 Excel 发送写命令。
不要向名称相似的其他 workbook 发命令，或通过界面自动化编辑单元格。
```

### 7. 可观察验收清单

- [ ] 明确写出适用理由：“用户显式标记 Microsoft Excel，或请求针对已打开、活动、已连接 workbook、选区或 add-in 的后续修改”。
- [ ] 只使用合成输入，并得到连接门槛、只读检查计划、预期变更 diff 及关键值/公式/视觉验收字段，不声称已修改工作簿。
- [ ] 检查“Computer Use 只用于设置与焦点，单元格读写必须走连接文档工具；任一设置门槛失败时停下，不能改写其他 workbook 或转本地文件”，没有向名称相似的其他 workbook 发命令，或通过界面自动化编辑单元格。

## SS03 Spreadsheets:电子表格

### 1. 用途

使用 loader 提供的 artifact-tool 创建、编辑、分析并验证独立电子表格文件。

### 2. 适用与不适用场景

- 适用：用户要独立 XLSX、XLS、CSV、TSV 或 Google Sheets-ready workbook，且没有 live Excel 目标。
- 不适用：用户明确要求控制 Excel desktop 中当前打开的工作簿。

### 3. 输入/输出

- 输入：源表或数据、工作簿结构、公式规则、格式、图表需求和最终文件目标。
- 输出：artifact-tool 调用方案、公式可追溯规则、关键范围检查和渲染验收清单（练习不生成工作簿）。
- 前置依赖：真实执行需要 load_workspace_dependencies 返回的 runtime 与 artifact-tool；课程不生成工作簿。

### 4. 最小调用模板

```text
@spreadsheets
请使用 $spreadsheets:Spreadsheets（Spreadsheets:电子表格；路径 slug: spreadsheets；调用名: Spreadsheets）。
任务：基于下方合成材料，写出使用 loader 提供的 artifact-tool 创建、编辑、分析并验证独立电子表格的方案；只列预期证据，不生成文件。
材料：<synthetic-fixture>
```

### 5. 边界与风险

必须使用 loader 提供的 @oai/artifact-tool；依赖缺失时报告阻塞，不能换 openpyxl 等库，读问题也不能擅自修改或导出。课程练习不得读取真实客户数据、凭据或生产状态，也不得发送、部署或写入外部系统。

### 6. 提示词练习

```text
$spreadsheets:Spreadsheets
这是一个完全虚构的文件练习：<synthetic-fixture>。
请先判断是否适用，再输出 artifact-tool 调用方案、公式检查和渲染验收清单；不要生成或导出工作簿。
不要硬编码派生值、忽略公式错误或在只读问答中改写文件。
```

### 7. 可观察验收清单

- [ ] 明确写出适用理由：“用户要独立 XLSX、XLS、CSV、TSV 或 Google Sheets-ready workbook，且没有 live Excel 目标”。
- [ ] 只使用合成输入，并得到 artifact-tool 调用方案、公式检查和渲染验收清单，不声称已生成工作簿。
- [ ] 检查“必须使用 loader 提供的 @oai/artifact-tool；依赖缺失时报告阻塞，不能换 openpyxl 等库，读问题也不能擅自修改或导出”，没有硬编码派生值、忽略公式错误或在只读问答中改写文件。
