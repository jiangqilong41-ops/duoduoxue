# 插件课程研究记录

快照日期：2026-07-20。来源为本机插件 manifest、canonical `SKILL.md` 和相邻 `agents/openai.yaml`；课程正文为中文概括，不复制上游全文。

## 盘点口径

- 纳入 19 个 manifest 与 127 个 canonical/nested skill。
- 排除 Ponytail `.openclaw/skills` 的 6 个平台镜像，以及插件根目录的 3 个 agent 配置。
- `status` 是当日 `codex plugin list` 的观察值，不代表课程运行保证。
- 路径均为插件根目录相对路径；未写入个人绝对路径。

## Manifest 快照

| plugin | version | status | license | author |
|---|---|---|---|---|
| mattpocock-skills | 1.2.0+codex.9603c1c | installed, enabled | MIT | {"name": "Matt Pocock", "url": "https://github.com/mattpocock"} |
| ponytail | 4.8.4 | installed, enabled | MIT | {"name": "Dietrich Gebert", "url": "https://github.com/DietrichGebert"} |
| data-analytics | 0.2.8-13ceeea1f599 | not installed | Proprietary | {"name": "Data Analytics Maintainers"} |
| openai-templates | 0.1.0 | not installed | Proprietary | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| hyperframes | 0.1.2 | not installed | Apache-2.0 | {"name": "HeyGen", "email": "hyperframes@heygen.com", "url": "https://hyperframes.heygen.com"} |
| product-design | 0.1.50 | not installed | Proprietary | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| sales | 1.0.8 | not installed | Proprietary | {"name": "OpenAI"} |
| documents | 26.715.12143 | installed, enabled | MIT | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| pdf | 26.715.12143 | installed, enabled | MIT | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| spreadsheets | 26.715.12143 | installed, enabled | MIT | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| presentations | 26.715.12143 | installed, enabled | MIT | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| template-creator | 26.715.12143 | installed, enabled | Proprietary | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| visualize | 1.0.12 | installed, enabled | Proprietary | {"name": "OpenAI"} |
| build-ios-apps | 0.1.2 | not installed | MIT | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| build-web-apps | 0.1.2 | not installed | MIT | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| browser | 26.715.52143 | installed, enabled | Proprietary | {"name": "OpenAI"} |
| chrome | 26.715.52143 | installed, enabled | Proprietary | {"name": "OpenAI"} |
| computer-use | 1.0.1000451 | installed, enabled | Proprietary | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |
| sites | 0.1.30 | installed, enabled | Proprietary | {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"} |

## Skill 清单

`skill_slug` 表示插件根目录下的相对目录名；显式调用时应以同一目录中
`SKILL.md` frontmatter 的 `name` 为准。`invocation_name` 列记录实际调用名，
因此可以清楚区分路径 slug 与接口名（例如 `shadcn-best-practices` 对应
`shadcn`）。
`display_name` 优先取相邻 `agents/openai.yaml` 的 `interface.display_name`；
文件不存在时回退到 `SKILL.md` frontmatter 的 `name`。因此 Browser 显示为
`Browser`，Chrome、Computer Use 与 Sites 单元分别显示为 `control-chrome`、
`computer-use`、`sites-building` 和 `sites-hosting`，不臆造缺失的界面元数据。

| plugin | skill_slug | invocation_name | display_name | relative_path | sha256 | license |
|---|---|---|---|---|---|---|
| mattpocock-skills | ask-matt | ask-matt | Matt Pocock:技能导航 | skills/ask-matt/SKILL.md | 645faa62b40b514c0d2630982ff5189982429959c85fcd2bcca14b27b44c49c8 | MIT |
| mattpocock-skills | code-review | code-review | Matt Pocock:双轴代码审查 | skills/code-review/SKILL.md | ecc52358306c96957147f2cef7354b424002617e3e74b69c9f000bf07f524c97 | MIT |
| mattpocock-skills | codebase-design | codebase-design | Matt Pocock:代码库设计 | skills/codebase-design/SKILL.md | a8d50abac5a4018f60e1d911d4b6f4e36454ca14d6c390c0695a578c7de65dad | MIT |
| mattpocock-skills | diagnosing-bugs | diagnosing-bugs | Matt Pocock:故障诊断 | skills/diagnosing-bugs/SKILL.md | f52623aa0c7bc967449ea4254f19572210301e2acb4681b4af81928697720717 | MIT |
| mattpocock-skills | domain-modeling | domain-modeling | Matt Pocock:领域建模 | skills/domain-modeling/SKILL.md | 152e2c97239affb12a60c5f4a7e74ab546a49ae169688c81f4e2ccc42dafa579 | MIT |
| mattpocock-skills | grill-me | grill-me | Matt Pocock:深度访谈 | skills/grill-me/SKILL.md | c9e49a07db94737dc7a3f240f63a2773bb474f890ba8bbaeb301211836453fab | MIT |
| mattpocock-skills | grill-with-docs | grill-with-docs | Matt Pocock:文档化深度访谈 | skills/grill-with-docs/SKILL.md | a0b34c865d2322bdf6a5d44bddd34ddfdd758038b4e87cd743b3b4c7d8d8e197 | MIT |
| mattpocock-skills | grilling | grilling | Matt Pocock:访谈引擎 | skills/grilling/SKILL.md | 44331dda57f461db4fec3f2efb6ddabe7aaaa0a57ae0f88a883bc61aed8a0587 | MIT |
| mattpocock-skills | handoff | handoff | Matt Pocock:任务交接 | skills/handoff/SKILL.md | aa365c9c3fb57b52e282d901dc2ed8153707b9f54d3fa2a5d15499c2768aaead | MIT |
| mattpocock-skills | implement | implement | Matt Pocock:规格实施 | skills/implement/SKILL.md | a49104e9e1d218c9e1c3288dfba4f0334c587c77f9f855e17b6da9ea6aca64fb | MIT |
| mattpocock-skills | improve-codebase-architecture | improve-codebase-architecture | Matt Pocock:代码库架构改进 | skills/improve-codebase-architecture/SKILL.md | f8ade0415df62ee0eebfb1256962ea6737abc4efe1199dae1a67ef351d1b1be3 | MIT |
| mattpocock-skills | prototype | prototype | Matt Pocock:原型验证 | skills/prototype/SKILL.md | 03074862d4b6e4eaf472aa75146e1d193dd9e3bba0e4303a9b2425562d1d44cc | MIT |
| mattpocock-skills | research | research | Matt Pocock:一手来源研究 | skills/research/SKILL.md | e1fd100708d22ca7c769679cbb6af795bf0adc453779487823b5f1003e7edb38 | MIT |
| mattpocock-skills | resolving-merge-conflicts | resolving-merge-conflicts | Matt Pocock:合并冲突解决 | skills/resolving-merge-conflicts/SKILL.md | c7c9ba81362a786aac05d2223123bf1bd2f8a99c3243a72882ede9c68bedfb24 | MIT |
| mattpocock-skills | setup-matt-pocock-skills | setup-matt-pocock-skills | Matt Pocock:技能初始化 | skills/setup-matt-pocock-skills/SKILL.md | d2f5c87f15460f7b90a25a8c539a57c1e6f71b5a51c3bb285060c219495d1cde | MIT |
| mattpocock-skills | tdd | tdd | Matt Pocock:TDD 测试驱动开发 | skills/tdd/SKILL.md | 5363bb2775679fe9311fbb67947f95359169c6e7f1fac77c0f25e190bca6cf2f | MIT |
| mattpocock-skills | to-spec | to-spec | Matt Pocock:规格整理 | skills/to-spec/SKILL.md | d6667433bc7fc8e94c4cba6a11b3ce7311dfb6d3a383760ac77030d4ffb915b4 | MIT |
| mattpocock-skills | to-tickets | to-tickets | Matt Pocock:任务拆分 | skills/to-tickets/SKILL.md | 31be19f2a4fb62b31314dbf491ca2c3113bb1d7ea317b840f99be2558934f019 | MIT |
| mattpocock-skills | triage | triage | Matt Pocock:事项分诊 | skills/triage/SKILL.md | b2c8375b4358b524722988c352b13e51af8227cc0ded12857e4033cd860d01ab | MIT |
| mattpocock-skills | wayfinder | wayfinder | Matt Pocock:大型工作导航 | skills/wayfinder/SKILL.md | af8dac9864c0e5cf460947244cfa3beecd7ee115f42e4668c7a9eae576073aa8 | MIT |
| mattpocock-skills | writing-great-skills | writing-great-skills | Matt Pocock:高质量技能编写 | skills/writing-great-skills/SKILL.md | 12ac7e78d161f84fb3c2011a8e4e6805a6b0f09412edaba149781a81079bd1f3 | MIT |
| ponytail | ponytail | ponytail | ponytail:极简模式 | skills/ponytail/SKILL.md | d1ffcddbc486ab787d5797441e8b6e4717da3249c6786b83fc2abd2f12803c29 | MIT |
| ponytail | ponytail-audit | ponytail-audit | ponytail:全库瘦身审计 | skills/ponytail-audit/SKILL.md | 5560b8e383dbe2ddfddc873a1e2bf2e586e23e0cd7d995537482b2315331f6d1 | MIT |
| ponytail | ponytail-debt | ponytail-debt | ponytail:简化债务台账 | skills/ponytail-debt/SKILL.md | c84fba75f0ca12bfe83f9a78ea02fd125c5dd3f1fbb18124105a489937f284e6 | MIT |
| ponytail | ponytail-gain | ponytail-gain | ponytail:收益看板 | skills/ponytail-gain/SKILL.md | 24e01d1c9715cb136ba1c4f1e52a95940c0193558b876828e537736480d6408b | MIT |
| ponytail | ponytail-help | ponytail-help | ponytail:帮助 | skills/ponytail-help/SKILL.md | 23ee3856c727129f87ab850985f9e9ed6368f10449816aa7ff043bf2dd45ab4d | MIT |
| ponytail | ponytail-review | ponytail-review | ponytail:复杂度审查 | skills/ponytail-review/SKILL.md | 40df33b58fc6ef889b93585733feb9566b76e9586efa7f376785c1e995197ac0 | MIT |
| data-analytics | analyze-data-quality | analyze-data-quality | Data Analytics:数据质量分析 | skills/analyze-data-quality/SKILL.md | 9a3c994f87da0c7a8c5ce37bbf08a59fc6f5b4f368475d3d7438f622b753d5f0 | Proprietary |
| data-analytics | build-dashboard | build-dashboard | Data Analytics:仪表板构建 | skills/build-dashboard/SKILL.md | c453ef3e1187477f696aae9a68b116d0e7e0bd6f665ab03a9d1634d13482aaaa | Proprietary |
| data-analytics | build-report | build-report | Data Analytics:分析报告构建 | skills/build-report/SKILL.md | 03db47974dc400b026d9268730de1ef317b5446a7a6bc9906ad471bfb117fd22 | Proprietary |
| data-analytics | report-to-google-doc | report-to-google-doc | Data Analytics:报告转 Google 文档 | skills/build-report/report-to-google-doc/SKILL.md | 0fac3acf39e180a8ee398c837cd40289c5e0f72473ef3788be623cb68e703a1f | Proprietary |
| data-analytics | report-to-google-slides | report-to-google-slides | Data Analytics:报告转 Google 幻灯片 | skills/build-report/report-to-google-slides/SKILL.md | 4dd1c74a3fc5284c3bf69500ff82213c0849663d15b79579e1e950cfa2558d2d | Proprietary |
| data-analytics | report-to-pdf | report-to-pdf | Data Analytics:报告转 PDF | skills/build-report/report-to-pdf/SKILL.md | ef65a78de9ca425698b529cbdaea7e6323ec6a704cbc10f070920ee6e8d11d57 | Proprietary |
| data-analytics | create-data-context | create-data-context | Data Analytics:数据上下文创建 | skills/create-data-context/SKILL.md | b004f792fa63e639dbce197562c97230eb58250e639b6bbe926085e3a44b0c2b | Proprietary |
| data-analytics | design-kpis | design-kpis | Data Analytics:KPI 设计 | skills/design-kpis/SKILL.md | fcefdecacd1d64f847fbb7c45e93a6bd49c679dff66b8966ebc74c4dc39b8f21 | Proprietary |
| data-analytics | gather-business-context | gather-business-context | Data Analytics:业务上下文收集 | skills/gather-business-context/SKILL.md | e8a1e917b8c4d03248987f33ca49fb7b1d6ed533328c39a02cafcc5b88b4577c | Proprietary |
| data-analytics | index | index | Data Analytics:分析工作流入口 | skills/index/SKILL.md | 2239188d6ac667a9e4b546ffb441f17ac3cfe90fe7683ac68506789ef8dabeb3 | Proprietary |
| data-analytics | jupyter-notebooks | jupyter-notebooks | Data Analytics:Jupyter 笔记本 | skills/jupyter-notebooks/SKILL.md | 8303d33041a5d5ccbfbb5addbb60bd8b0559027f01a586f98b7728e58c4127ed | Proprietary |
| data-analytics | kpi-reporting | kpi-reporting | Data Analytics:KPI 汇报 | skills/kpi-reporting/SKILL.md | a4ee918f3c87af4db8bb007cf8fefec444cd47b96b76de711349f11d7232861a | Proprietary |
| data-analytics | market-sizing | market-sizing | Data Analytics:市场规模估算 | skills/market-sizing/SKILL.md | dd353ab8c7229d3bc831234725db7d02ceeb1a889ee781103f90997879ac1951 | Proprietary |
| data-analytics | metric-diagnostics | metric-diagnostics | Data Analytics:指标诊断 | skills/metric-diagnostics/SKILL.md | c9293227b592328c06cb9f6a2f23c0114ddcd1ca456a42f1ceebfe5981007314 | Proprietary |
| data-analytics | product-business-analysis | product-business-analysis | Data Analytics:产品与业务分析 | skills/product-business-analysis/SKILL.md | 3e6b684ace151bbf777afd88fe34758b337ac0d6ff2bf332958d7a495d624a4b | Proprietary |
| data-analytics | publish-artifact-to-sites | publish-artifact-to-sites | Data Analytics:分析成果发布 | skills/publish-artifact-to-sites/SKILL.md | 26b3846191d1c5237262a26da61694aa67bef38c4ed03eb3167e39f39c6f07a3 | Proprietary |
| data-analytics | validate-data | validate-data | Data Analytics:分析验证 | skills/validate-data/SKILL.md | 7aa5c77b22b9e5bf1b054e4ab6320a12dfd5342aa6cb18f8e497b46c713be20e | Proprietary |
| data-analytics | visualize-data | visualize-data | Data Analytics:数据可视化 | skills/visualize-data/SKILL.md | ff2601669022a2ef43524e0225eb4833acc03260db90b996a2d6f74fbbce7b12 | Proprietary |
| openai-templates | artifact-template-analytics-dashboard | artifact-template-analytics-dashboard | OpenAI Templates:分析仪表盘 | skills/artifact-template-analytics-dashboard/SKILL.md | cf5360fd8b197673bb237c52c603c97fa319c875c3dfa2cd8efff52d4422f513 | Proprietary |
| openai-templates | artifact-template-business-review | artifact-template-business-review | OpenAI Templates:商业回顾 | skills/artifact-template-business-review/SKILL.md | 27721fc1d67d1b41949caa75ac8f94f81952ff124406878af6524047929e60d2 | Proprietary |
| openai-templates | artifact-template-design-report | artifact-template-design-report | OpenAI Templates:设计报告 | skills/artifact-template-design-report/SKILL.md | 563722f53854e606f8a9f87e37e72d7ef70a22d46d5836b8e4d6abfb1b79e9e0 | Proprietary |
| openai-templates | artifact-template-experiment-analysis | artifact-template-experiment-analysis | OpenAI Templates:实验分析 | skills/artifact-template-experiment-analysis/SKILL.md | 0b05effc47df0a14f8e0c3e3597e6722224747435546385d38a2cae279bd20b9 | Proprietary |
| openai-templates | artifact-template-financial-budget | artifact-template-financial-budget | OpenAI Templates:财务预算 | skills/artifact-template-financial-budget/SKILL.md | c0b6b7a62a15597aaf2b1ec679e21da48f533b756127f0aef957cdfe9f3da738 | Proprietary |
| openai-templates | artifact-template-investment-committee-memo | artifact-template-investment-committee-memo | OpenAI Templates:投委会备忘录 | skills/artifact-template-investment-committee-memo/SKILL.md | 68abd08cfe5e073e3c446a3f675f44c5bf98f57434dba679e8acd8a763379a8b | Proprietary |
| openai-templates | artifact-template-legal-memorandum | artifact-template-legal-memorandum | OpenAI Templates:法律备忘录 | skills/artifact-template-legal-memorandum/SKILL.md | 51fb9d21baf6119c4ccb1903638a6bac0e859210de63460fffa7025d52e997e0 | Proprietary |
| openai-templates | artifact-template-market-trends-report | artifact-template-market-trends-report | OpenAI Templates:市场趋势报告 | skills/artifact-template-market-trends-report/SKILL.md | d58d019b89cb6f292ac3ab991d561489eef477ff53ce05fb024a0c936f5af26a | Proprietary |
| openai-templates | artifact-template-minimal-letterhead | artifact-template-minimal-letterhead | OpenAI Templates:简洁信头 | skills/artifact-template-minimal-letterhead/SKILL.md | 880ef094d4d0c89a7bde5ce9bbe4086625c186651e9e6efc8ba8bdd7cc77f9d5 | Proprietary |
| openai-templates | artifact-template-operating-calendar | artifact-template-operating-calendar | OpenAI Templates:运营日历 | skills/artifact-template-operating-calendar/SKILL.md | 33bb660791a0b9a21628a42c34934932220203b6aabd84e98cb1b45327d0384c | Proprietary |
| openai-templates | artifact-template-operating-review | artifact-template-operating-review | OpenAI Templates:运营回顾 | skills/artifact-template-operating-review/SKILL.md | 6d63c5cd025ffe936e7bab5db3023672bbaec26af55c2bb8b057d38c202c9c32 | Proprietary |
| openai-templates | artifact-template-project-kickoff | artifact-template-project-kickoff | OpenAI Templates:项目启动 | skills/artifact-template-project-kickoff/SKILL.md | aa893ebd89e7c8d1db4261d01cc2b1add35d78d00785871ccaaa5fc8db783ec9 | Proprietary |
| openai-templates | artifact-template-project-tracker | artifact-template-project-tracker | OpenAI Templates:项目追踪 | skills/artifact-template-project-tracker/SKILL.md | d97d5be20189b7f53dd269b6e1c5f694eaf53e5a72f6559fcb1578911b7cda82 | Proprietary |
| openai-templates | artifact-template-sales-pipeline | artifact-template-sales-pipeline | OpenAI Templates:销售管道 | skills/artifact-template-sales-pipeline/SKILL.md | 15cfeeedf440021f16ed3f3ad8c7c1ef6d48898b9447741e223d2fb41cfc9800 | Proprietary |
| openai-templates | artifact-template-simple-dark-mode | artifact-template-simple-dark-mode | OpenAI Templates:简洁暗色演示 | skills/artifact-template-simple-dark-mode/SKILL.md | b7c8d0c05f75878b9bc21e56a57c41ec1aa29700aca0a24822be0f9f1bd53207 | Proprietary |
| openai-templates | artifact-template-simple-light-mode | artifact-template-simple-light-mode | OpenAI Templates:简洁浅色演示 | skills/artifact-template-simple-light-mode/SKILL.md | 7c68430c6cf57b55b457d4735dbd1a46b889bef135a32222902dd0848b6e1752 | Proprietary |
| openai-templates | artifact-template-strategy-memorandum | artifact-template-strategy-memorandum | OpenAI Templates:战略备忘录 | skills/artifact-template-strategy-memorandum/SKILL.md | 51d7882ac94e8e57b323394825728c33925af878806e37277217c2dc12a912e5 | Proprietary |
| openai-templates | artifact-template-system-design | artifact-template-system-design | OpenAI Templates:系统设计 | skills/artifact-template-system-design/SKILL.md | 87f7b7ed1b0d8410f5e5971cd7f7db9a4165e2f37069e97e52dbfb469b75a57c | Proprietary |
| openai-templates | artifact-template-team-alignment | artifact-template-team-alignment | OpenAI Templates:团队对齐 | skills/artifact-template-team-alignment/SKILL.md | 26d7cafdcd1899a937b325c5d02ac57c162d45002153be33a934d35f81eb6110 | Proprietary |
| openai-templates | artifact-template-three-statement-forecast | artifact-template-three-statement-forecast | OpenAI Templates:三表预测 | skills/artifact-template-three-statement-forecast/SKILL.md | 74f4a5cccec0107b861548b157e04c51d9b58ec13a990c86394b4c529b8ecf41 | Proprietary |
| hyperframes | gsap | gsap | HyperFrames:GSAP 动画参考 | skills/gsap/SKILL.md | 730476ba02cc56c8a59b3e4a897801923f463289cd386bccb56d01833be4441f | Apache-2.0 |
| hyperframes | hyperframes | hyperframes | HyperFrames:HyperFrames 视频制作 | skills/hyperframes/SKILL.md | ce7dbbc9229a8fbf3e0dea8724bd8bbf8b059c031ac8be717a283a246b5355d8 | Apache-2.0 |
| hyperframes | hyperframes-cli | hyperframes-cli | HyperFrames:HyperFrames 命令行 | skills/hyperframes-cli/SKILL.md | 253ff75cd896b2290e5247c4ec63fc1341ac14d891fd5fb06ba04e59e49e4ab5 | Apache-2.0 |
| hyperframes | hyperframes-registry | hyperframes-registry | HyperFrames:HyperFrames 组件库 | skills/hyperframes-registry/SKILL.md | 0248bfb9968d53ea8f9e4b5f7f5a8eb9e72f21108022580f7eba2fba7e26b234 | Apache-2.0 |
| hyperframes | website-to-hyperframes | website-to-hyperframes | HyperFrames:网站转 HyperFrames 视频 | skills/website-to-hyperframes/SKILL.md | 482afa42349ff391de892565334b17f68f7d52f4f32e5266c05065b574c860ee | Apache-2.0 |
| product-design | audit | audit | Product Design:产品体验审计 | skills/audit/SKILL.md | 616e74f59da25ae72f5c853b7c9cfc4317400d224ff162abd67293b6f3ee1c82 | Proprietary |
| product-design | design-qa | design-qa | Product Design:设计还原质检 | skills/design-qa/SKILL.md | a761ed96e1e91905e7e6f32ab95e8dc6d0cca2036556d4d63945b25efd3eaa5c | Proprietary |
| product-design | get-context | get-context | Product Design:确认设计简报 | skills/get-context/SKILL.md | 19a38a3ac4443cb477a01c2303e77c891c304234a195dd2da248e3e736b22679 | Proprietary |
| product-design | ideate | ideate | Product Design:视觉方案构思 | skills/ideate/SKILL.md | 595f83f18e22b19f32fe858530f17572d3ec25d7c7f3b2dc305eca41e5435d33 | Proprietary |
| product-design | image-to-code | image-to-code | Product Design:图像转代码 | skills/image-to-code/SKILL.md | e0acaa600fda4b87b58774cf60a5fda8b98e18990d4d51920ec40773dd97971c | Proprietary |
| product-design | index | index | Product Design:产品设计 | skills/index/SKILL.md | 8f9f19273ee34a06298ed93f8d70a9c17b3d4ce66f061b024f6d1038b138e5f7 | Proprietary |
| product-design | research | research | Product Design:产品体验研究 | skills/research/SKILL.md | bf824e72dd93941c8d591e4af13bb7e3a09380cd6ed7dd8c1f61a295648fa023 | Proprietary |
| product-design | share | share | Product Design:原型分享 | skills/share/SKILL.md | 5976cfbc9d865230db085af37f0c25a2d8beed3ff58e0e2edb9d0a4f7ca987b5 | Proprietary |
| product-design | url-to-code | url-to-code | Product Design:网址转代码 | skills/url-to-code/SKILL.md | 8708f622b4c86866370b8c1cef5f404b71679d09e6678953b2ca7125c3c1098d | Proprietary |
| product-design | user-context | user-context | Product Design:产品设计上下文 | skills/user-context/SKILL.md | 5690a7f99cf896970493f5d0bd7f35f62ab9cbe21744352acf84dc0ceea4194c | Proprietary |
| sales | analyze-account-signals | analyze-account-signals | Sales:客户信号分析 | skills/analyze-account-signals/SKILL.md | 47b9998f0c467d10f3852741b6ac2cd495790d68354318a67ae00b566d647912 | Proprietary |
| sales | answers-ask-user-input | answers-ask-user-input | Sales:用户信息补充 | skills/answers-ask-user-input/SKILL.md | 520b201f5ef23875b1ed1170a90c3ab9e02b5ca36ddf6d1ea3a2e0bf38c41400 | Proprietary |
| sales | apollo | apollo | Sales:Apollo 使用指南 | skills/apollo/SKILL.md | 11fc2423543596fa1203b1d27fb45f08075cf2c473ed9a3bc66b2f87eb665263 | Proprietary |
| sales | build-business-case | build-business-case | Sales:商业论证构建 | skills/build-business-case/SKILL.md | f50445d05863e237a5e07f8276ec54468681d14cd3af82bb1d8e0a0f59ffd32f | Proprietary |
| sales | build-competitive-brief | build-competitive-brief | Sales:竞品简报构建 | skills/build-competitive-brief/SKILL.md | a053187e4f51216c15a4ebdd562b55cb5985af4a35beabcb89e152b6ec132195 | Proprietary |
| sales | enrich-company-and-contact-data | enrich-company-and-contact-data | Sales:企业与联系人数据丰富 | skills/enrich-company-and-contact-data/SKILL.md | 072fb8571e9e8b03e2d4812aac93c68dd490d1a5996f5c529062bdc50e8a6a3c | Proprietary |
| sales | find-customer-quotes | find-customer-quotes | Sales:客户引言查找 | skills/find-customer-quotes/SKILL.md | 237307a11621dd2aea507e4790f07a50d73be146cccfdce3b5a321b73f38c6b3 | Proprietary |
| sales | find-key-internal-sources | find-key-internal-sources | Sales:内部关键来源查找 | skills/find-key-internal-sources/SKILL.md | b63612463f882a63c49454c3da192d35bcc3bb0171496a564059b8c821f54c50 | Proprietary |
| sales | follow-up-after-call | follow-up-after-call | Sales:通话后跟进 | skills/follow-up-after-call/SKILL.md | 986d21b8fd8876aa35807eaff74b027341c6f288d75592d350a00bf184032824 | Proprietary |
| sales | get-rep-call-feedback | get-rep-call-feedback | Sales:销售通话反馈 | skills/get-rep-call-feedback/SKILL.md | 6722491c123ed970f60733ab4f76ffe03017d2c710f5c358499a48d9db9f9df3 | Proprietary |
| sales | hubspot | hubspot | Sales:HubSpot 使用指南 | skills/hubspot/SKILL.md | 2a9571967ab27e1653d819cb89e496b96905437ed286d5a5ad7d7c41062c8f82 | Proprietary |
| sales | index | index | Sales:销售工作流入口 | skills/index/SKILL.md | 682e48bdffddd02cca24f412a36de668dfc661e908c78e32430d71a1b1b6e573 | Proprietary |
| sales | plan-deal-strategy | plan-deal-strategy | Sales:商机策略规划 | skills/plan-deal-strategy/SKILL.md | 74ed63a46e76320fde0732ea7e63f8ce076812592bffc5ca0348cdcc6999bcb6 | Proprietary |
| sales | prepare-for-meeting | prepare-for-meeting | Sales:会议准备 | skills/prepare-for-meeting/SKILL.md | 6089e76a257cb779825be89c09e11deb499a2d9c3691c59e064e02bd9eb446ef | Proprietary |
| sales | prioritize-accounts | prioritize-accounts | Sales:客户优先级排序 | skills/prioritize-accounts/SKILL.md | d5005c70d1a12eee07c764d1072602251a043b53d39c5a7715479d1390113c4c | Proprietary |
| sales | review-forecast | review-forecast | Sales:销售预测审查 | skills/review-forecast/SKILL.md | b066f82a9a94f1beacabb6c0b75650c63bc1db2f5cea24986441b07d161bc548 | Proprietary |
| sales | review-rep-call-trends | review-rep-call-trends | Sales:销售通话趋势审查 | skills/review-rep-call-trends/SKILL.md | 93dbaf5c3f2125897ffdd738f97be6e5e778ec44c03bee7319830c63ced643eb | Proprietary |
| sales | sales-company-research | sales-company-research | Sales:目标企业研究 | skills/sales-company-research/SKILL.md | c2127a18a4f1c5d36f6bc72fe2ac30878286f809878ad0240ec8dc39f3578c74 | Proprietary |
| sales | salesforce | salesforce | Sales:Salesforce 使用指南 | skills/salesforce/SKILL.md | 0640253e4a68d06f09522a7d275213d3c78b849439139d223d2f7b32a3e64a63 | Proprietary |
| sales | zoominfo | zoominfo | Sales:ZoomInfo 使用指南 | skills/zoominfo/SKILL.md | b5fce52852fb593dfbd1e74e85cc940e58569d22a77a2365f13bd7e875b32dcf | Proprietary |
| documents | documents | documents | Documents:文档处理 | skills/documents/SKILL.md | 8ed9ed302b578fe7eedd420ed1fc01fd8304c66d2b397ec9a1cdc98780b9cb52 | MIT |
| pdf | pdf | pdf | PDF:PDF 文件 | skills/pdf/SKILL.md | b09cb414c60234a15599c04a502ce36fe6e9aa178aabe007e43a3346b5aab607 | MIT |
| spreadsheets | excel-live-control | excel-live-control | Spreadsheets:Excel 实时控制 | skills/excel-live-control/SKILL.md | 994e33cf1d3352d3fb4ab9e3f24076b63ecd0a92dae450f2b4a27cd9a7f00e88 | MIT |
| spreadsheets | spreadsheets | Spreadsheets | Spreadsheets:电子表格 | skills/spreadsheets/SKILL.md | 98c8106e5f0d9f9fa44c027037ac32d800f30af3707584d9b74688563b51d2d1 | MIT |
| presentations | presentations | Presentations | Presentations:演示文稿 | skills/presentations/SKILL.md | 2c7a19e3b20c3361139849d73920e94478922c3330e1bc3d0a477021a6d0ea62 | MIT |
| template-creator | template-creator | template-creator | Template Creator:模板创建器 | skills/template-creator/SKILL.md | d39cc27dd2b84f564b37284dcb75dc20e75d117e7ad5b2d84b01223a0e6f509e | Proprietary |
| visualize | visualize | visualize | Visualize | skills/visualize/SKILL.md | 6b96bc46f40d6f0d0264f01bf268fa6648dc5b12121e4bceaa8803d1415afbde | Proprietary |
| build-ios-apps | ios-app-intents | ios-app-intents | Build iOS Apps:App Intents 集成 | skills/ios-app-intents/SKILL.md | ecfa87ec1070bccfdfa0d21ee997bbfbfd78edfb1f22da5da9c05ff006e9fa52 | MIT |
| build-ios-apps | ios-debugger-agent | ios-debugger-agent | Build iOS Apps:模拟器调试 | skills/ios-debugger-agent/SKILL.md | bb8ad932ec473cee097c9c8d106051134e9ab6cf9dc85d6a8e62ce80ad24c385 | MIT |
| build-ios-apps | ios-ettrace-performance | ios-ettrace-performance | Build iOS Apps:ETTrace 性能分析 | skills/ios-ettrace-performance/SKILL.md | 1888c0b2fc6b7d9f3d54d06333e9628a2c4660b9d9b5ddf3edc37f126c773935 | MIT |
| build-ios-apps | ios-memgraph-leaks | ios-memgraph-leaks | Build iOS Apps:Memgraph 泄漏分析 | skills/ios-memgraph-leaks/SKILL.md | f09a1e78c00b342196035f6570723f16e40e34a800d353c7c885d1dab4dc8781 | MIT |
| build-ios-apps | ios-simulator-browser | ios-simulator-browser | Build iOS Apps:模拟器浏览器 | skills/ios-simulator-browser/SKILL.md | f3f0216323cd7713a73f1bc4beee1b740a7867f20affef331760dd1932a1ec4b | MIT |
| build-ios-apps | swiftui-liquid-glass | swiftui-liquid-glass | Build iOS Apps:SwiftUI 液态玻璃 | skills/swiftui-liquid-glass/SKILL.md | 8e9ec37d9b6ed146672faf12c88be61d367c280ab6159bfbc7726a122030b78b | MIT |
| build-ios-apps | swiftui-performance-audit | swiftui-performance-audit | Build iOS Apps:SwiftUI 性能审计 | skills/swiftui-performance-audit/SKILL.md | 6fc6bd4d49b49ccb2089be706c449f195daa7db2c36d8097d883426488eb4b1a | MIT |
| build-ios-apps | swiftui-ui-patterns | swiftui-ui-patterns | Build iOS Apps:SwiftUI 界面模式 | skills/swiftui-ui-patterns/SKILL.md | a96f078512c6c679a3504ec20e0eedff4a9be3a06eb9a95107f3556c081bb708 | MIT |
| build-ios-apps | swiftui-view-refactor | swiftui-view-refactor | Build iOS Apps:SwiftUI 视图重构 | skills/swiftui-view-refactor/SKILL.md | 129cbb511987985ed7bf9e3f20443632a7becdf0c2824ded6b52241cc339243a | MIT |
| build-web-apps | frontend-app-builder | frontend-app-builder | Build Web Apps:前端应用构建器 | skills/frontend-app-builder/SKILL.md | 9273de02827b29534be28fb2b37154c1571ac38b4e20d3ef5482b7e22af67394 | MIT |
| build-web-apps | frontend-testing-debugging | frontend-testing-debugging | Build Web Apps:前端测试调试 | skills/frontend-testing-debugging/SKILL.md | 03724620cf7e7de425b607a5492f572d867b1cf5d9c92c74bf50d057d7415e0b | MIT |
| build-web-apps | react-best-practices | react-best-practices | Build Web Apps:React 最佳实践 | skills/react-best-practices/SKILL.md | cc7d03309817f392c419a203e1bc1f1759ef94831f7dbedf39d91a35ac5bc86a | MIT |
| build-web-apps | shadcn-best-practices | shadcn | Build Web Apps:shadcn/ui 组件管理 | skills/shadcn-best-practices/SKILL.md | 7678f5168d4ee6f3ae3ce4d3d41c654f0aebc7b88cbc392a9504822dec0dff28 | MIT |
| build-web-apps | stripe-best-practices | stripe-best-practices | Build Web Apps:Stripe 最佳实践 | skills/stripe-best-practices/SKILL.md | 5062f0c980030af377a0ac33b77c9d233676e2ecbb57b3d3cd8734fc0da464b2 | MIT |
| build-web-apps | supabase-best-practices | supabase-postgres-best-practices | Build Web Apps:Supabase Postgres 最佳实践 | skills/supabase-best-practices/SKILL.md | cfc4da3ed47c14f4fb24c5b4db4be443fa200e12e71d674fb1270eecce87a302 | MIT |
| browser | control-in-app-browser | control-in-app-browser | Browser | skills/control-in-app-browser/SKILL.md | 80c5a591bb761f7242f480fc4fc6883860f303f3d5a91e5714230c7897ad8a8d | Proprietary |
| chrome | control-chrome | control-chrome | control-chrome | skills/control-chrome/SKILL.md | b4b06a14ab8ed5ab7d5a57ae78253e0b7625dab7e52249e8e17798c2b783eb26 | Proprietary |
| computer-use | computer-use | computer-use | computer-use | skills/computer-use/SKILL.md | 2cc1d04e978ca5204dc19184ef947e5f1bd4886ab47c521faca00b5807492894 | Proprietary |
| sites | sites-building | sites-building | sites-building | skills/sites-building/SKILL.md | be568720e1e1a7577ff3f5826b75abdcd0d06affd6cf2b10ff5245bc3aec9d2b | Proprietary |
| sites | sites-hosting | sites-hosting | sites-hosting | skills/sites-hosting/SKILL.md | e1cd0842e1426204dbfc856e7bd7f364ee671fe6df78c6458c9a4d5e49b496e3 | Proprietary |

## 参考链接

仅在 skill 明确依赖外部产品时，按实验手册中的单元说明补充官方文档；本清单本身不把外部链接当作版本身份。
