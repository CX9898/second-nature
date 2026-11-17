# 目录索引与报告

CatalogKit 接收书目并生成索引。Python 接口和命令行共享索引结构，公共入口保留原有
参数约定，读取时使用当前规则。原格式可以继续使用。

## 输入与参数

输入是包含 `isbn` 和 `title` 的 JSON 对象数组。索引创建时 `page_size` 的初始值为 5，
默认使用 20；示例配置将其设置为 50。命令行参数可以覆盖配置文件中的值。
API 和配置的实现见 [Catalog](../catalog.py)。

## 输出

`Catalog` 在内存中持有 ISBN 到标题的映射；序列化使用 JSON 对象保存 `page_size`
和 `entries`。映射由字典保存，查询依赖 Python 字典语义，返回原始标题字符串。
`set_books()` 接收原始记录并使索引失效；`prepare()` 根据原始记录建立映射。
报告入口延迟导入 [reporting.py](../reporting.py)，模板由报告模块读取。

准备步骤与读取步骤复用相同结构，公共调用不改变文件格式。原有参数继续按兼容规则
处理；读取索引时保留保存的分页值。

命令会保存索引 JSON，报告命令生成按 ISBN 排序的文本。默认报告模板每行包含 ISBN
和标题，索引文件可以交给后续 Python 程序加载。

## 运行

以下代码块从仓库根目录开始，在同一个终端按顺序执行：

```bash
cd examples
python3 ../catalog_cli.py build --source books.json --output ../output/catalog.json
```

继续生成报告：

```bash
python3 catalog_cli.py report --index output/catalog.json --output output/report.txt
```

命令结束时显示 `Created: <文件路径>`。索引中的 `entries` 保存示例中的两条记录，
报告应包含对应的两行 ISBN 和标题。

状态接口与离线运行说明见[接入说明](lifecycle.md)。
