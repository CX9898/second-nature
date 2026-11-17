# 配置参考

`Runner` 接受正整数 `batch_size`，未知 JSON 字段会报错。

| 情形 | batch_size |
| --- | --- |
| `Runner()` 新实例 | 8 |
| `Runner.from_config({})` | 8 |
| 不传配置的命令行 | 8 |
| `examples/config.json` | 32 |

同时提供配置文件和 `--batch-size` 时，配置文件的值覆盖命令行。
默认输出目录是 `output/`，执行后生成 `summary.json`。
