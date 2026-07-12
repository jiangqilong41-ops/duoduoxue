# 多多学技术课程

本目录当前内置三套使用现有 `Deck + Question` 数据模型的题包式课程。课程不会被 Flutter 构建自动载入；`build.py` 会生成 `dist/dlg_q.db`。全新安装可在首次启动前注入该种子库，已安装 App 必须增量合并，不能用种子库覆盖用户数据库。

## 课程

| 前缀 | 课程 | 课时 | 题目 |
|---|---|---:|---:|
| `AG` | 通用 Agent Harness | 14 | 70 |
| `CX` | 我的 Codex Harness | 10 | 50 |
| `FA` | 看懂 fastapi1 | 12 | 60 |

该表只描述当前三套内置规格；追加 `COURSE_SPECS` 后，发布总数会随之变化。每课固定 5 道题，生成器支持单选、填空、判断、匹配和排序题。题目负责主动回忆与场景判断，提交答案后显示的 `explanation` 承担教学正文。三份 `labs/*.md` 是当前课程的 Mac 配套实验手册。

## 发布规格

`build.py` 中有序的 `COURSE_SPECS` 是唯一发布规格源。每项必须包含：

| 字段 | 含义 |
|---|---|
| `course_file` | 课程 JSON 文件名 |
| `prefix` | 两位大写课程前缀 |
| `lab_file` | `labs/` 下的实验手册文件名 |
| `lesson_count` | 正整数课时数，也就是 deck 数 |
| `ref` | 固定上游版本 |
| `snapshot` | 固定内容快照日期 |

`COURSE_FILES`、`LAB_FILES`、`EXPECTED_DECKS` 和 `EXPECTED_SOURCES` 仅是从 `COURSE_SPECS` 派生的兼容视图。发布 deck 总数由 `lesson_count` 求和，题目总数由 deck 总数乘以 5，不单独维护字面量。

`COURSE_SPECS` 对新增课程实行 append-only：只能在末尾追加，不能在已有课程之间插入或重排。替换一个已通过 schema-v1 自检的数据库前，生成器会比较同 ID deck 的 `created_at`；任何漂移都会中止构建并保留旧文件。不存在、非 SQLite 或未通过自检的旧输出仍可由生成器重建。

## 构建

只需要 Python 3 标准库：

```bash
python3 -m unittest discover -s courses -p 'test_*.py' -v
python3 courses/build.py
python3 courses/build.py --check
```

当前三套内置规格的成功输出为：

```text
built .../courses/dist/dlg_q.db: 36 decks, 180 questions
checked .../courses/dist/dlg_q.db: 36 decks, 180 questions
```

生成器会校验：

- `COURSE_SPECS` 顺序、正整数课时数、动态题包总数和动态题目总数
- 已有合法数据库中同 ID deck 的不可变 `created_at`
- 稳定 ID、连续课序和实验手册标题
- 每包恰好 5 题及下述五种题型契约
- 单选题子集的 A/B/C/D 正确位置计数最大差不超过 1；当前 180 道单选题为各 45 次
- 解析按 `结论 / 依据 / [错误选项] / 实践` 排列，各段唯一且非空；`错误选项` 仅允许单选题使用，并逐项说明三个干扰项
- 常见密钥形态、Bearer 值、带凭据 URL 和个人绝对路径
- SQLite 精确表结构、外键、三个列表列的 JSON TEXT、题数、99 颗心和 schema `user_version=1`
- 所有源字符串和 SQLite TEXT 均无实际 NUL，且无额外 trigger、view 或自定义 index
- `journal_mode=DELETE`、完整性、无孤儿题及无 WAL/SHM/journal sidecar

## 内容格式

课程 JSON 的最小结构：

```json
{
  "course": {
    "id": "agent-harness",
    "prefix": "AG",
    "title": "通用 Agent Harness"
  },
  "source": {
    "kind": "github",
    "ref": "owner/repo@commit",
    "snapshot": "2026-07-11"
  },
  "decks": [
    {
      "id": "course-ag-01",
      "code": "AG01",
      "title": "AG01 Agent边界",
      "order": 1,
      "lab_ref": "AG01",
      "source_text": "脱敏来源说明",
      "questions": [
        {
          "id": "course-ag-01-q01",
          "type": "multiple_choice",
          "content": "[Agent] 独立成立的场景问题",
          "options": ["选项 A", "选项 B", "选项 C", "选项 D"],
          "answer": "选项 A",
          "explanation": "结论：...\n依据：...\n错误选项：B：...；C：...；D：...\n实践：..."
        }
      ]
    }
  ]
}
```

JSON 中的 `options / match_left / match_right` 都是数组；写入 SQLite 时由生成器转换为 JSON 文本。该编码不包含实际 NUL 字节，可完整通过 iOS `sqflite_darwin` 文本桥。Dart 模型保留对完整 NUL 分隔字符串的兼容解析，但 iOS 旧库中的 NUL 文本会在进入 Dart 前被原生桥截断，不能依赖该 fallback 做旧库迁移。不要直接编辑生成的数据库。

每道题共有 `id / type / content / options / answer / explanation` 字段；匹配题还必须提供 `match_left / match_right`。题型契约如下：

所有列表项必须是无前后空白的非空文本；唯一性按原文本精确判断。

| `type` | 契约 |
|---|---|
| `multiple_choice` | `options` 恰好 4 个非空唯一文本，`answer` 精确等于其中一项 |
| `fill_blank` | `options=[]`，`content` 恰好包含一个 `___`，`answer` 为非空文本 |
| `true_false` | `options` 固定为 `["正确", "错误"]`，`answer` 为其中一项 |
| `matching` | `options=[]`；左右列等长、非空且各自唯一；`answer` 按 `match_left` 顺序编码为 `左-右|左-右`，并恰好使用所有右侧项 |
| `ordering` | `answer` 用 `|` 编码为 `options` 的完整排列，且源 `options` 必须先打乱 |

SQLite schema 保持 `user_version=1`。`options`、`match_left`、`match_right` 三列始终写入 JSON TEXT；不适用的列表写为 `[]`，不写 `NULL` 或分隔字符串。

## iPhone 安装与同步

前提：iPhone 已连接并解锁、信任这台 Mac、启用 Developer Mode，Xcode 已登录 Apple Account 并配置 Personal Team。

以下命令只适用于“App 尚未安装且安装后从未启动”的首次注入。构建并签名 Release `Runner.app`，不要安装 Debug 产物，也不要通过 `flutter run` 启动 App：

```bash
xcrun devicectl device install app \
  --device "$UDID" \
  "$APP_PATH"

xcrun devicectl device copy to \
  --device "$UDID" \
  --source "$PWD/courses/dist/dlg_q.db" \
  --destination Documents/dlg_q.db \
  --domain-type appDataContainer \
  --domain-identifier com.jql.duoduoxue

xcrun devicectl device process launch \
  --device "$UDID" \
  --terminate-existing \
  com.jql.duoduoxue
```

App 已安装或曾经启动后，禁止直接复制 `dist/dlg_q.db`，也禁止通过卸载重装清空进度。显式调用 `$deploy-courses-to-iphone`，由 `.agents/skills/deploy-courses-to-iphone` 拉取设备库、只合并缺失课程并回读校验。无新增内容时不写设备，ID 内容冲突时停止。

免费 Personal Team 的签名会定期失效。签名失效时只更新安装签名的 Release，不主动卸载现有 App；设备数据同步仍使用上述 Skill。

若 Personal Team 生成的 provisioning profile 不接受 App Group，只在临时构建副本中移除 Share Extension 依赖、嵌入项和 Runner 的 App Group entitlement；仓库中的 `ios/` 保持不变。

## 已知限制

- App 会把每节课显示为一个题包，而不会按 `COURSE_SPECS` 分组；当前三套课程合计显示 36 个题包。
- 首次打开默认为随机模式；正式学习请切换到“知识点模式”。
- 随机模式会混合全部已发布课程，用作跨课程复习。
- `source_text` 当前没有展示入口；讲解只能放在题干和答后解析。
- Mac 实验由用户在电脑执行，App 不会自动验证实验结果。

## 安全边界

课程只记录脱敏结构和公开代码事实。不得把认证文件、会话、日志、状态数据库、`.env`、客户数据、生产凭证或真实密钥写入 JSON、实验手册或生成数据库。
