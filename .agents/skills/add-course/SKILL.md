---
name: add-course
description: Use when adding, drafting, registering, or validating a course in this repository, including course JSON, mixed question types, lab manuals, or the generated seed database.
---

# Add Course

## Overview

为 `duoduoxue` 新增可重复构建的题包课程。课程源、实验手册和注册项必须一起交付，生成数据库不是可手工编辑的源文件。

## Workflow

1. 在仓库根目录工作。先读 `courses/build.py` 的 `COURSE_SPECS`、现有相邻课程及 [课程契约](references/course-contract.md)。
2. 明确课程标题、事实来源、唯一两字母前缀、正整数课时数、来源 ref 和独立 snapshot。来源无法核实时先停止，不编造材料。
3. 先为新规格或校验行为补失败测试，再创建 `courses/<name>.json` 和 `courses/labs/<name>.md`，并更新 `courses/README.md` 的课程表。
4. 每课恰好 5 题，按内容选择题型。不要为了平均分配而扭曲内容；选择题正确位置在全部选择题子集中保持最大计数差不超过 1。
5. 只在现有有序 `COURSE_SPECS` 末尾追加一个规格项。不得插入中间或重排旧项，否则会改变既有 deck 的稳定 `created_at`。不要创建第二个目录、映射或总数常量。
6. 运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s courses -p 'test_*.py'
python3 courses/build.py
python3 courses/build.py --check
```

7. 复核 diff：原有课程内容不应变化；不得出现密钥、凭证 URL、Bearer 值、真实客户数据或 `/Users/<name>` 绝对路径。

## Guardrails

- ID 使用 `course-<prefix小写>-NN` 与 `course-<prefix小写>-NN-qNN`，课时 `order` 从 1 连续递增。
- `created_at` 由生成器按 `COURSE_SPECS` 顺序计算，不写进 JSON。
- 每道题必须能独立理解；解析依次且各一次使用 `结论：`、`依据：`、`实践：`，每段非空。
- 选择题还必须逐项解释三个错误选项；其他题型不添加虚假的错误选项段落。
- 不直接修改 `courses/dist/dlg_q.db`，不修改 App schema，也不在本 Skill 中触碰 iPhone。
- 完成新增课程后，仅提示用户显式调用 `$deploy-courses-to-iphone`；不得自动部署。
