# LabelDock 制作入口

从本交付根目录执行；相对路径以当前工作目录解析。输入须为 UTF-8，恰有 name、team 两列且两项均非空；CLI 固定使用 table，姓名中的逗号须用 CSV 引号保护。预览输出路径必须不存在。

```bash
labeldock build labels.csv --out preview.json
labeldock check preview.json
```

build 只保存不可变预览，不写出 HTML；源 CSV 修改只影响下一次 build，已有预览不会更新，重新生成须使用新预览文件名。
必须校验将交付的同一预览，只有 pass 才可交给写出入口；校验只检查必填字段和页内布局，不核对姓名或部门是否真实，也不证明已经打印。
将该预览交给接收人员；接收人员无需原始 CSV，但仍须对将写出的同一预览取得 pass。
