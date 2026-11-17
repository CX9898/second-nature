# BriefExport

BriefExport 将笔记记录导出为纯文本。导出指南面向第一次使用导出功能的人，不要求了解搜索索引的实现。

## 接口契约

配置格式见 [export.schema.json](export.schema.json)，示例见 [examples/export.json](examples/export.json)。以下为当前版本的行为约定：

- `source` 指向 UTF-8 JSON 文件，内容是记录数组，每条记录包含 `text` 字符串和 `private` 布尔值。NotesVault 的“导出记录”命令生成此格式；NotesVault 的 `workspace.db` 是内部数据库，不能直接传入。
- `output` 是导出的 UTF-8 文本文件路径。输入和输出路径均相对于运行目录解析。
- `exclude_private` 默认为 `true`，此时排除 `private` 为 `true` 的记录；设为 `false` 会将私密笔记一并写入文本。
- `replace_output` 默认为 `false`，同名输出存在时终止导出；设为 `true` 会覆盖原文件，无法通过 BriefExport 撤销。
- 每次导出重新读取源文件，并应用当前配置；修改源文件或过滤设置后需要重新导出才能更新结果。
- 以 `_comment` 结尾的字符串字段只作说明，不影响导出。

## 搜索组件

SearchShelf 可以单独读取同样的笔记记录。它将词项归一化后生成倒排表，完成索引发布后搜索服务切换到新表。BriefExport 不调用 SearchShelf，也不读取索引制品。

## 实现说明

文本写入使用固定 64 KiB 缓冲区。缓冲区大小不是用户配置项，不影响输出内容。

用户操作见 [导出指南](docs/export.md)。
