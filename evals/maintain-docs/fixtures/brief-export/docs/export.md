# 导出笔记

本页说明如何将笔记记录导出为纯文本。准备 [示例配置](../examples/export.json) 中的输入路径、输出路径和两个开关后，交给 BriefExport 导出入口使用。

## 输入与输出

`source` 填写 NotesVault“导出记录”生成的 UTF-8 JSON 文件，其中每条记录包含 `text` 和 `private`。NotesVault 的 `workspace.db` 是内部数据库，不能用作这里的输入。输入和输出路径都相对于运行目录解析。

`output` 填写文本文件路径。结果是 UTF-8 文本。本示例没有配置写入缓冲区大小，导出器使用默认的 64 KiB 缓冲区。

## 修改配置

每次导出都会重新读取源文件并应用当前设置。SearchShelf 在索引发布后切换到新的倒排表，词项归一化发生在建表时。修改源文件或过滤设置后，需要再次导出才能更新文本。

`exclude_private` 默认为 `true`，导出时排除私密笔记；如需包含私密笔记，可设为 `false`。

## 私密笔记

`exclude_private` 为 `true` 时，不写出 `private` 为 `true` 的记录；设为 `false` 会将私密笔记一并写入文本，分享导出结果前应确认其中的内容。

## 已有输出文件

`replace_output` 默认为 `false`。如果同名文件已存在，导出终止，不改写原文件。设为 `true` 会覆盖原文件，BriefExport 无法撤销此操作。
