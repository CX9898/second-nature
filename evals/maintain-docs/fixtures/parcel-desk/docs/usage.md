# 分组与检查

`read_parts()` 读取零件 CSV，按包裹编号分组，保留每个零件的名称和重量。
`read_checks()` 把检查 CSV 的每行转换为一个布尔值，按文件顺序返回。

示例 `part-checks.csv` 为 `parts.csv` 的每条零件记录提供一个检查值。可以使用以下
流程读取、分组，再将检查值传给包裹检查接口：

```python
from parcel import check_parcels, read_checks, read_parts

parcels = read_parts("examples/parts.csv")
checks = read_checks("examples/part-checks.csv")
print(check_parcels(parcels, checks))
```

如果没有检查结果，省略 `checks` 仍可统计包裹数：

```python
print(check_parcels(parcels))
```

另一个输入 `parcel-checks.csv` 已按包裹编号的排序提供检查值，可以替换示例中的
检查文件。包裹检查返回包裹数；提供检查值时还返回接受的包裹数。
