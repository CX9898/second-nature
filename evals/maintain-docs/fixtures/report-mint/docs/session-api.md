# 在服务中复用报表会话

`ReportSession` 供需要保留已加载事件、连续生成多份报表的服务使用。
字段含义和报表格式见 [接口契约](../contract.json)。

## 首次生成

新会话尚未加载事件，也没有准备好的窗口。先加载事件、选择窗口长度，
再准备窗口并写出报表：

```text
session = ReportSession()
session.load_events("events.json")
session.set_window_minutes(60)
session.prepare_windows()
session.write_report("reports/hourly.txt")
```

`set_window_minutes()` 接受正整数，单位为分钟；省略设置时使用 30。
它也可以在加载事件前调用。`prepare_windows()` 要求已调用 `load_events()`，
空事件数组同样可以准备，写出时得到空报表。

## 修改已使用的会话

改变窗口长度会使已准备的窗口失效。复用上面的会话生成十五分钟报表时：

```text
session.set_window_minutes(15)
session.prepare_windows()
session.write_report("reports/quarter-hour.txt")
```

如果改值后直接调用 `write_report()`，SDK 会抛出 `WindowsNotPrepared`，不写文件。
`prepare_windows()` 使用当前已加载的事件和当前窗口长度重新计算。

`load_events()` 会替换全部已加载事件，并使窗口失效，因此重新加载后也要先调用
`prepare_windows()`。修改磁盘上的源文件不会自动更新会话；需要再次加载才能读到变化。
事件和窗口长度都未改变时，可以直接多次调用 `write_report()` 写到不同路径。

## 写出文件

输出目录需要事先存在。`write_report()` 的 `overwrite` 参数默认为 `false`，
同名文件存在时失败并保留原文件。传入 `overwrite=true` 会覆盖旧文件，
不保留历史版本，也无法撤销。相对路径以服务当前工作目录为基准。
