# 课程契约

## 文件与注册

- JSON 顶层仅含 `course`、`source`、`decks`。
- `course` 含 `id`、`prefix`、`title`；`prefix` 是全局唯一的两个大写字母。
- `source` 含 `kind`、`ref`、`snapshot`，必须对应实际取材快照。
- 每个 deck 含 `id`、`code`、`title`、`order`、`lab_ref`、`source_text`、`questions`。
- 实验手册必须为每个 `lab_ref` 提供 `## <CODE>` 标题，Mac 命令默认只读且无破坏性。
- `COURSE_SPECS` 是唯一注册表。复制现有项并填写课程文件、前缀、实验手册、课时数、ref、snapshot、`curriculum_order`、`phase`、`bridge_ref`，只能追加到末尾；不得插入或重排旧项。物理发布顺序负责稳定 `created_at`，逻辑主线按连续唯一的 `curriculum_order` 排序。

## 通用题目字段

基础字段为 `id`、`type`、`content`、`options`、`answer`、`explanation`。`content` 延续现有课程标签格式，字符串和数组元素均不得为空或包含实际 NUL 字符，列表项不得有前后空白。

| type | 契约 |
| --- | --- |
| `multiple_choice` | `options` 为 4 个唯一文本，`answer` 与其中一项完全相同。解析逐项说明其余 A/B/C/D 三项为何错误。 |
| `fill_blank` | `options=[]`；`content` 恰好出现一个 `___`；`answer` 非空。 |
| `true_false` | `options=["正确","错误"]`；`answer` 必须是其中之一。 |
| `matching` | `options=[]`，另含 `match_left`、`match_right`；两侧非空、等长且各自唯一，不得包含保留分隔符 `|`。`answer` 按 `match_left` 顺序写成 `左-右|左-右`，每个左右项恰好使用一次。 |
| `ordering` | `options` 非空且不得包含保留分隔符 `|`；`answer` 以 `|` 编码 `options` 的完整排列；初始 `options` 不得已经是正确顺序。 |

每课固定 5 题，但无需五种题型各出现一次。题型应服务于学习目标。

## 内容验收

- 问题脱离前后顺序仍能作答，只有一个满足契约的答案。
- 事实题能追溯到 `source` 或实验手册，实践命令不读取凭证、日志、状态库、`.env`、客户数据或生产数据。
- 新课时数量只要求为正整数；发布总题包数和题数由 `COURSE_SPECS` 计算。
- SQLite 的 `options`、`match_left`、`match_right` 由生成器编码为 JSON TEXT，`PRAGMA user_version` 保持 1。
