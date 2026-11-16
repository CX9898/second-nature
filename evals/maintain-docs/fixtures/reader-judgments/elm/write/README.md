# LabelDock 写出入口

从本交付根目录执行；相对路径以当前工作目录解析。将收到的不可变预览放为 preview.json；无需原始 CSV，也无需重新构建。
写出前必须校验将写出的同一预览，只有 pass 才能继续；校验只检查必填字段和页内布局，不核对姓名或部门是否真实，也不证明已经打印。

```bash
labeldock check preview.json
```

确认返回 pass 后再执行：

```bash
labeldock emit preview.json --out labels.html --replace
```

默认拒绝已有 HTML，示例的 --replace 会不可撤销覆盖 labels.html，且无回滚；校验前提不满足时失败且不改动已有 HTML。写出成功仅表示 HTML 已保存，不表示已经打印或人工核对。
