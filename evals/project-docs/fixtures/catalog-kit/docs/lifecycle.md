# Python 接入与离线运行

本页供将 CatalogKit 接入应用的开发者使用。Python 3.10 或更高版本即可在源码目录运行，
不需要第三方 Python 包。

## 索引来源

`Catalog.set_books()` 接收原始书目，`prepare()` 根据这些记录建立索引。
`Catalog.load()` 从保存的索引文件创建实例；`set_index()` 可以接收调用方提供的现成映射。
应用通过 `lookup()` 查询，通过 `save()` 保存。

这里需要补充各条路径中哪些步骤是必需的、什么时候能直接查询，以及修改书目后的处理。
示例记录和已有索引分别位于 [books.json](../examples/books.json) 和
[saved-index.json](../examples/saved-index.json)。

## 离线报告

索引构建命令使用 [catalog_cli.py](../catalog_cli.py) 和 [catalog.py](../catalog.py)。
报告命令还会加载 [reporting.py](../reporting.py)。需要说明离线复制时的文件范围，
以及已有索引能否直接生成报告。
