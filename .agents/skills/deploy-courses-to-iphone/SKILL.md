---
name: deploy-courses-to-iphone
description: Use when the user explicitly requests deploying newly built duoduoxue courses to a physical iPhone.
---

# Deploy Courses To iPhone

## Overview

将种子库中的缺失题包增量合并到真机数据库。设备上只要存在有效 `dlg_q.db` 就始终以它为基底；只有 App 已安装、无匹配进程、数据库不存在且无 sidecar 时才可首次注入。写入失败后先拉取并分类当前库，默认不覆盖；任何冲突、sidecar、schema、新鲜度或回读异常都必须停止并保留证据。

## Invocation Gate

只在用户显式调用 `$deploy-courses-to-iphone` 时执行。普通的“新增课程”、构建或校验请求不得隐式同步设备。

## Required Workflow

1. 先运行课程测试、`python3 courses/build.py` 和 `python3 courses/build.py --check`。
2. 阅读并逐项执行 [真机同步流程](references/device-workflow.md)。只接受唯一一台状态可用的物理 iPhone。先区分未安装、已安装、签名失效；App 已安装时再以 `Documents/dlg_q.db` 是否存在区分未初始化首次注入与设备库增量。
3. 已安装路径先终止 App 并确认进程消失，再检查 `Documents`。数据库不存在且无三种 sidecar 时可进入首次注入；数据库存在且无 sidecar 时先拉取并完整校验，有效库走增量。损坏库若有上次首次注入保留的原先不存在证据和 seed 哈希，则进入首次注入失败分类；否则停止。
4. 合并：

```bash
python3 .agents/skills/deploy-courses-to-iphone/scripts/merge_course_db.py \
  --device-db "$device_db_copy" \
  --seed-db courses/dist/dlg_q.db \
  --output "$merged_db"
```

5. JSON 结果含非空 `warnings` 时停止并保留其中的 0700 staging 路径；不得写设备。无 warning 且新增数为 0 时不写设备。存在新增时，紧邻首次写回前必须重新确认进程消失、无 sidecar，并拉取 `prewrite.db` 与最初快照逐字节比较；任何不新鲜迹象都禁止写回。若 App 曾重启，下一次必须新建 `$work` 并从第 1 节开始，不能从拉库步骤续跑。
6. 从首次 `copy to` 命令本身开始，增量或 seed 的写入、回读、`cmp`、完整校验任一失败都必须重新静止 App、重查 sidecar 并分类。增量失败分类每次创建唯一 `failure-attempt.*`，不得覆盖历史；观察到进程、sidecar、canonical 缺失或新鲜度变化时立即创建唯一只读 `backup-stale/event.*`。不得自动写回 seed 或旧 backup；当前有效库优先保留并作为下一次增量基底，无法判定时保留现场、停止且不启动 App。
7. 只有增量成功、确认 no-op，或首次注入并回读成功后才可启动 App。launch 成功后才可删除含设备数据的 `$work`；launch 失败保留并报告，清理失败报告残留绝对路径。

## Non-Negotiable Rules

- 不覆盖 `user_stats`、`study_records`、已有 `mastery_level`、已有题包更新时间或用户自建题包。
- 已存在 ID 的不可变内容不同时停止；不更新、不删除、不猜测哪一份较新。
- 正常已安装 App 不得重装。全新未安装时才可安装签名 Release；已安装但未初始化时不重装，可在严格写入门禁后继续首次注入；签名失效时只可用相同 bundle id 的签名 Release 覆盖续签，绝不卸载，再按数据库是否存在返回首次注入或增量流程。
- 两种 Release 例外都禁止 Debug。Personal Team 不支持 App Group 时，只在临时仓库副本排除 Share Extension 和 App Group，原仓库必须保持不变。
- `dlg_q.db` 一旦存在就禁止 seed 覆盖，唯一例外是首次注入失败后：保留证据证明目标原先不存在、seed 哈希吻合，且用户再次明确确认无需保留任何进度并授权替换。该人工恢复仍必须重新静止、回读和完整校验。
- 旧 backup 永不自动恢复。`backup-stale` 是不可清除或覆盖的 sticky 证据；人工恢复默认拒绝任何 marker。只有展示全部 event 后，用户再次逐项点名承认每个变化并明确授权丢失其后进度，才可在唯一 `restore-attempt.*` 中记录哈希回执后继续。
- 人工恢复先分别解析分类和授权时的文件 JSON。只有两次都 present 才拉取并 `cmp` canonical DB，两次都 absent 才跳过；状态不同立即写 sticky marker 并停止，禁止无条件执行必失败的拉取。
- 设备不可用、多设备、App 无法终止或复查仍在运行、sidecar 存在、快照不新鲜、备份失败或回读失败时停止并保留 `$work`。
