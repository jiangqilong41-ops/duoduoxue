# Harness 与本地 Skills 课程研究记录

快照日期：2026-07-20。所有路径均相对来源根目录；不记录用户绝对路径、凭证值、环境变量值、运行日志、状态数据库或客户数据。

## 来源快照

| course | source root | ref | units |
|---|---|---|---:|
| GS | `$CODEX_HOME` | `codex-cli-0.144.6` | 23 skills |
| FS | `fastapi1` repository | `fastapi1@710807b32a2a7af6b48496390d15c728a8afd06b` | 8 skills |
| FH | `fastapi1` repository | `fastapi1@710807b32a2a7af6b48496390d15c728a8afd06b` | 12 components |

## GS：用户级与系统 Skills

| skill | relative_path | sha256 |
|---|---|---|
| academic-research-suite | skills/academic-research-suite/SKILL.md | ac99405283a786683b21b2f3743211c31b1571fa0be09d2ea8213e33997808e4 |
| cataloging-agent-framework-configs | skills/cataloging-agent-framework-configs/SKILL.md | 36d78b0a47720bdfb55642796197616a54fdebcec22d439ead10f6e247c3409e |
| chinese-openai-yaml | skills/chinese-openai-yaml/SKILL.md | 2d7c530e1ca33ffed3cabb34a96e8848303efada3bda5e62a9c8d8ff265bf5fa |
| chronicle | skills/chronicle/SKILL.md | 34a478a3087a226204ddee293dd1d2fbe726bef581435ed9fc7f2f0a0f45a6fd |
| cli-creator | skills/cli-creator/SKILL.md | b060caa0ba6bca224be46ca908eee7aaab380db9513a5a4e4c196236fa4d3430 |
| ec-public-customer-task | skills/ec-public-customer-task/SKILL.md | 680f26e50f940381b51b66d34600192b759c590c20ba9940447990169d81a724 |
| fastapi1-email-marketing | skills/fastapi1-email-marketing/SKILL.md | d7a951ec93b28e2bbbb171256c2dfc60566f50897968056f9bfd10ef3984aec3 |
| fastapi1-skill | skills/fastapi1-skill/SKILL.md | cfbe0a70b780612b7facee0464cc8cc63558668cb73c0018324ece661b2b249b |
| fastapi1-wechat-marketing | skills/fastapi1-wechat-marketing/SKILL.md | 6d0705a120ea8a304dfa993aec1a558aa25e2681ad7e721701fe27115e6353f5 |
| fastapi1-wxcli | skills/fastapi1-wxcli/SKILL.md | 784b83c0a55a9380148ee61a6543f97f810dd67e165dca1088689d435ab804ee |
| frontend-design-ultimate | skills/frontend-design-ultimate/SKILL.md | 7d55854616a3d28ba55d32b8ae22c5ea5292e385b3eca0e462c3bce1fcb2a9a0 |
| graphify | skills/graphify/SKILL.md | 20ea867e9b98eab045835a14efb5f4360cb916b90ff9e44f0f8c1049fe0ded3c |
| hightech-enterprise-certification | skills/hightech-enterprise-certification/SKILL.md | 5e8b23bd135145691b53c1404ce3d00cbc5b1867f547169b4c7065cee7bff3c4 |
| html-a4-print | skills/html-a4-print/SKILL.md | dfacef8508c38da091f69f7894c0d24de533fcdedbf3d3421cf8187875f4835b |
| memory-leak-debugging | skills/memory-leak-debugging/SKILL.md | ffd210f68a94c8398926381929df439f1ba2ab036a0ddc7b01bcf56c94c1bd28 |
| stop-slop | skills/stop-slop/SKILL.md | 7432a1d9ebdd42b27666da8458af252edf549f723fb14bcd4791425103930310 |
| teach | skills/teach/SKILL.md | a2c0ea56e28b01448cce9284946be9a49f0b722510fd1f58fd06ace428388a4e |
| imagegen | skills/.system/imagegen/SKILL.md | 59981d23519222bcecf1be48bb37730bbc50539ceb0e35ad09fcef98a3df19d3 |
| openai-docs | skills/.system/openai-docs/SKILL.md | 9914a79e6e1bd70d780b777e9019677af0eba60bbdfac3b7fe9b0407f16b5cc4 |
| plugin-creator | skills/.system/plugin-creator/SKILL.md | 8fd56316b2c49cbdc657a5d197967a233018e1fada65b00a5dd030dce6499a6e |
| review-agent | skills/.system/review-agent/SKILL.md | 07079efd0dc76f05fade424e5dfb048dce1de2df7626e1a4f56292a4f3f92228 |
| skill-creator | skills/.system/skill-creator/SKILL.md | da44c88f6b3845a8fa8c60792ec9a722110a55a9793c279757b48fefb11f819c |
| skill-installer | skills/.system/skill-installer/SKILL.md | d68b77e5bbb34dedab89d134da52855f140fc4b4299b80104f534e3b9e98f8ee |

## FS：fastapi1 项目 Skills

课程顺序与根 `AGENTS.md` 的触发矩阵一致；相邻 `agents/openai.yaml`
依次给出课程中的八个中文展示名。SHA-256 对应表内 `SKILL.md` Git blob。

| skill | relative_path | sha256 |
|---|---|---|
| source-driven-development | .agents/skills/source-driven-development/SKILL.md | c8544d01d61b9155effa080bfd3e335958fae57adada05cd4e78de7169e78ccd |
| frontend-ui-engineering | .agents/skills/frontend-ui-engineering/SKILL.md | 3881e53e53cfde95bf0cb16488c48690569932a38247ac65ab2db7332f2332d0 |
| security-and-hardening | .agents/skills/security-and-hardening/SKILL.md | 75b9b050847e729ce2499ca63ac457fae007b9f60045403c564887c303d5a452 |
| performance-optimization | .agents/skills/performance-optimization/SKILL.md | 55c8df656be30edbd80a3aa69c00046dfd2162c4707897aef37b15302a5acb8a |
| harness-maintenance | .agents/skills/harness-maintenance/SKILL.md | 70d5a5a11fe095848b4082526e7ee71678199c6abd18dcd7797335e468656c67 |
| git-branch-pr-merge | .agents/skills/git-branch-pr-merge/SKILL.md | fd25147e05bc331566670a4f5f34144a8ea24d598988016088c665190e0b2168 |
| windows-vm-operator | .agents/skills/windows-vm-operator/SKILL.md | 4560cc16adfa7497db2a292f9e901b6210f23f1c211c91d325fa2eecf323cb45 |
| remote-server-operator | .agents/skills/remote-server-operator/SKILL.md | 77d14c67120ca1153be95ec50616fa08eb01ecc7d382918033841b38724b3ff1 |

## FH：fastapi1 Codex Harness 来源文件

| component | relative_path | sha256 |
|---|---|---|
| AGENTS | .codex/AGENTS.md | 0dd2a333b5e9b87c0e91bee566e343d518ebb4de311a8c256f473a227c6326ec |
| data_security | .codex/agents/data_security.toml | 807a945b0b490a263bb438455f98e049d6af20dadba0f26ea5f6b53cc3188006 |
| docs_researcher | .codex/agents/docs_researcher.toml | 6481c4e03e4f93b7b196bee014ad6d4921d2321a86ead2dc34064af01018c011 |
| explorer | .codex/agents/explorer.toml | 072b01fbd11ef421f54e282de011635a8d21946a84830780a8f5afcfa77b7f3c |
| fastapi_api | .codex/agents/fastapi_api.toml | 339e15f7638be57e97910e42e60b913ef11e39498f016fb82a0e8b07271acb62 |
| reviewer | .codex/agents/reviewer.toml | 999ae5841a4ebe8049f95434da07a23bfec399c6861b21ed8016224ceb61c797 |
| config | .codex/config.toml | 8977bad4c1c144bf14b7cafb923abb1204116cf88e66dcf90bb18741e08eb88e |
| contract | .codex/contract.json | 5c5c0a1435ef7f042dbef2ab0fc86387db516067d56bd8ce96c441094d8b3285 |
| hooks | .codex/hooks.json | 8873aacb21e445981c03e30aa1763be46fb9989b64f1a38f77f6b9f9a9fae3fd |
| session_start | .codex/hooks/session_start.py | d6d90e8dad1c2ec56e2c1ae4c3f9f4688e6ad2fe222dd793ffd6dcf083e998d1 |
| environment | .codex/environments/environment.toml | dada36c114c58a7b6b0a4a8a55410986c3a78de433a87bf1135e03956937e77d |
| postgres_from_env | .codex/mcp/postgres_from_env.py | 962cf06172fe5ebb70e364c4a48ebb76d2155202154995f949b99670812234e4 |
| default rules | .codex/rules/default.rules | 6fa3471a517b18d26edfe6dfedb0b6c15c5c41413bd99c5ecfcaa5a071ab9243 |

固定提交中共有 13 个唯一 Harness 来源文件，映射为 FH02–FH13 的 12 个组件单元：两个 Hook 文件共同构成 FH10；`config.toml` 作为同一来源分别支撑 FH08 的项目配置视角和 FH12 的 MCP 视角，FH12 还联合 PostgreSQL wrapper。这里是来源复用，不是把同一个 config 文件重复计数为两个来源。

## FH：12 个组件单元与角色边界

| unit | component | source scope | course boundary |
|---|---|---|---|
| FH02 | AGENTS 范围 | `.codex/AGENTS.md` | 治理与作用域指令，不是命令拦截器或执行器 |
| FH03 | data_security | `.codex/agents/data_security.toml` | 只读数据/安全分析；不回显秘密、不修复 |
| FH04 | docs_researcher | `.codex/agents/docs_researcher.toml` | 只读一手资料核验；不实现、不复制 MCP 凭证 |
| FH05 | explorer | `.codex/agents/explorer.toml` | 只读代码勘探；不改状态、不替主线程决策 |
| FH06 | fastapi_api | `.codex/agents/fastapi_api.toml` | 只读 API 合同核对；不修改 route/schema/model |
| FH07 | reviewer | `.codex/agents/reviewer.toml` | 只读 findings；不提交修复或批准发布 |
| FH08 | 项目 config | `.codex/config.toml` | repo-specific 声明；不证明插件、MCP 或 agent 已运行 |
| FH09 | 结构化 contract | `.codex/contract.json` | 结构化期望事实；不启动任何组件 |
| FH10 | SessionStart Hooks | `.codex/hooks.json`、脚本 | 上下文注入声明；不替代权限、Rules 或业务鉴权 |
| FH11 | environment action | `.codex/environments/environment.toml` | 本地启动声明；课程不启动进程或访问端口 |
| FH12 | MCP 配置 | config MCP 表、PostgreSQL wrapper | 核对名称、最小权限和秘密流；不读 `.env`、不连接或调用 |
| FH13 | Rules | `.codex/rules/default.rules` | 命令 prefix guardrail；不替代 sandbox、approval 或测试 |

## MCP 与 Hooks 脱敏结构

| scope | kind | names/events | course boundary |
|---|---|---|---|
| user Codex | configured MCP | context7, openaiDeveloperDocs, sqlite, tavily, node_repl, computer-use (disabled) | GS/CX 只讲选择、配置层与证据；不复制 env/args 值 |
| fastapi1 | required MCP | openaiDeveloperDocs, postgresql, redis, sqlite | FH MCP 单元；PostgreSQL 只说明 wrapper 与 restricted 模式，不读取 `.env` |
| fastapi1 | project Hook | SessionStart (`startup|resume|clear`) | FH Hooks 单元；只验证定义和预期上下文 |
| ponytail | plugin Hooks | SessionStart (`startup|resume|clear|compact`), SubagentStart, UserPromptSubmit | PT01；插件携带、信任、启用、执行分别取证 |

## 排除项

- 不展开 `academic-research-suite` 内部 vendored 上游文件；只把顶层 `SKILL.md` 作为一个课程单元。
- 不读取或复制 `$CODEX_HOME/config.toml` 的值，只记录课程需要的 MCP 名称和启用/禁用结构。
- 不把 `.codex/agents/*.toml` 伪装成 skill；它们是只读角色配置。
- 不执行 Hook、MCP、安装器、生产运维、Windows VM、营销发送、CRM 写入或站点部署。
