# 内部运行手册

部署目标为 `10.20.0.12`，工作目录为 `/srv/samplekit`，任务输入为 `/srv/samplekit/inbox/data.json`。
这些地址和目录是内部操作目标，供值班维护者定位服务。

执行统计前确认输入是 JSON 数组，输出目录属于当前任务。

```bash
cd /srv/samplekit
python3 tool.py --input inbox/data.json --output-dir jobs/current
```

清理残留容器和镜像：

```bash
docker system prune --all --force
```
