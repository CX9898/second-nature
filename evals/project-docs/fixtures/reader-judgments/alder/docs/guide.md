# 铭牌操作

以下命令在交付根目录使用；相对输入输出路径均以当前工作目录解析。

## 生成预览

输入须为 UTF-8，恰有 name、team 两列且两项均非空；CLI 固定使用 table，姓名里的逗号须用 CSV 引号保护。SDK 构造默认 profile=plain，列名缓存起初为空，首次读取后记录两列位置。预览输出路径必须不存在，源 CSV 修改只影响下一次 build，已有预览不会更新；重新生成时须使用新预览文件名。

```bash
labeldock build labels.csv --out preview.json
```

build 只保存不可变预览，不写出 HTML。写出前必须校验将写出的同一预览，只有 pass 才能继续；校验只检查必填字段和页内布局，不核对姓名或部门是否真实，也不证明已经打印。

## 校验并写出

写出前必须校验将写出的同一预览，只有 pass 才能继续；校验只检查必填字段和页内布局，不核对姓名或部门是否真实，也不证明已经打印。

```bash
labeldock check preview.json
```

确认返回 pass 后再执行：

```bash
labeldock emit preview.json --out labels.html --replace
```

写出无需原始 CSV。默认拒绝已有 HTML，示例的 --replace 会不可撤销覆盖 labels.html，且无回滚；校验前提不满足时失败且不改动已有 HTML。模块初始化时版式缓存为空，第一次写出会缓存内置版式。写出成功仅表示 HTML 已保存，不表示已经打印或人工核对。
