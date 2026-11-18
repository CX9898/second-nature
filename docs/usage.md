# 使用指南

本指南适用于本地 Codex 和 Claude Code。先获取仓库副本，在仓库根目录运行以下命令。安装脚本只需 Python 3.10 或更高版本。

## 一键安装

在 Windows PowerShell 中，将仓库中的全部技能安装到 Codex 用户级目录。

```powershell
py -3 scripts/install.py
```

在 Linux 或 macOS 终端中，运行同一个脚本。

```sh
python3 scripts/install.py
```

如果系统通过 `python` 提供 Python 3.10 或更高版本，也可以用 `python scripts/install.py`。

将下面的参数加在本机的安装命令末尾，可选择客户端、技能或安装位置。

| 要做什么 | 添加的参数 |
| --- | --- |
| 安装全部技能到 Claude Code | `--client claude` |
| 只安装 `project-docs` 到 Codex | `project-docs` |
| 只安装 `project-docs` 到 Claude Code | `--client claude project-docs` |
| 安装到指定的技能目录 | `--dest "/path/to/project/.agents/skills"`（换成实际路径） |

`--dest` 直接指定目标目录，与 `--client` 二选一。相对路径以运行命令的目录为基准。

[安装脚本](../scripts/install.py) 自动查找带有 `SKILL.md` 的 [`skills/<name>/`](../skills/) 目录，复制整个技能目录，包括许可证和引用文件。终端用 `INSTALLED`、`UPDATED` 或 `SKIP` 显示每个技能的结果。安装失败时查看 `ERROR` 行定位原因。

如需在安装前检查本地修改过的技能，先按[基础校验](authoring.md#基础校验)运行校验器。

## 安装位置

| 客户端 | 用户级技能目录 | 项目级技能目录 |
| --- | --- | --- |
| 本地 Codex | `~/.agents/skills/` | 项目内的 `.agents/skills/` |
| 本地 Claude Code | `~/.claude/skills/` | 项目内的 `.claude/skills/` |

用户级技能可在多个项目使用。安装到单个项目时，将 `--dest` 指向该项目的技能目录。客户端发现规则见 [OpenAI 文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)和 [Claude Code 文档](https://code.claude.com/docs/en/skills)。

默认安装到 `~/.agents/skills/`。如果该目录没有同名项，脚本会沿用旧目录 `$CODEX_HOME/skills/`（默认 `~/.codex/skills/`）里的同名安装。两处都有同名技能时，脚本只处理 `~/.agents/skills/` 中的版本，Codex 仍可能显示两项。旧目录的兼容读取见 [Codex 源码](https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/host_roots.rs)。

Claude.ai、Cowork 和云端会话有各自的配置方式。请按对应环境的文档安装。

## 确认可用

先在客户端的技能列表中查找已安装的技能。找不到时，按客户端文档刷新或新建会话。再用真实请求检查技能是否被选中，以及任务结果是否符合预期。记录方式见 [评测指南](../evals/README.md)。

## 更新与卸载

更新本地仓库副本后，再运行安装命令即可补装新增技能并更新已有技能。脚本以当前仓库副本为准。已有安装一致时跳过，有差异时将旧副本备份到技能目录旁的目录，再安装仓库中的版本。安装中断后可重跑同一命令。

要恢复旧版本，先移走当前安装目录，再将 `UPDATED` 行标出的备份目录移回原安装位置。如果重跑时出现 `BACKUP` 行，旧版本的备份路径见该行。

脚本更新带有 `SKILL.md` 的普通安装目录。同名的其他文件或目录，以及内容有差异的链接安装，会报错并保留原项。卸载时仅移除对应技能目录。

## 客户端扩展

`agents/openai.yaml`、Claude 专用字段和权限配置各有语义，需要时按对应客户端版本添加。插件市场、连接器或 hooks 等能力可另加平台包装，核心技能仍保留在 `skills/`。分发方式的设计依据见 [设计说明](design.md)，客户端行为以适用版本的公开文档和实现为准。
