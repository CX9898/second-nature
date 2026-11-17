# ReportMint

ReportMint 读取本地事件记录，按固定分钟窗口统计事件数，输出 UTF-8 文本报表。
本页面向第一次使用 `reportmint render` 的读者。

## 准备配置

事件文件是 UTF-8 JSON 数组，每条记录包含带时区的 ISO 8601 时间字符串 `at`，例如：

```json
[{"at": "2026-10-01T08:10:00Z"}, {"at": "2026-10-01T08:45:00Z"}]
```

将事件文件保存为工作目录中的 `events.json`，并事先创建输出目录 `reports`。
在 [示例配置](examples/report.json) 中选择窗口长度和输出路径。
配置中的路径相对于运行命令的工作目录解析。
[接口契约](contract.json) 记录当前版本的字段与行为。

## 生成报表

在已安装 ReportMint 的环境中，从工作目录运行：

```bash
reportmint render --config examples/report.json
```

本示例将结果写入 `reports/hourly.txt`。报表只包含有事件的窗口，
每行给出窗口起始时间和事件数，时间统一以 UTC 表示。
`overwrite` 默认为 `false`，同名文件存在时命令失败并保留原文件。
设为 `true` 会覆盖原文件，不保留历史版本。

每次命令新建一个 `ReportSession`，读取本次源文件、应用配置、准备窗口后写出报表。
修改源文件或配置后，重新运行命令才会生成新的结果。

需要在服务中复用会话生成多份报表时，参见 [会话 SDK](docs/session-api.md)。
