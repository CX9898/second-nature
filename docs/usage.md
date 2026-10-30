# 使用指南

本文说明如何把一个已完成的技能安装到本地 Codex 或 Claude Code。先按 [编写指南](authoring.md#环境准备) 准备环境，从 [skills/](../skills/) 选择技能。以下命令均从仓库根目录执行，以 `maintain-docs` 为例；安装其他技能时替换对应名称。

## 选择安装位置

仓库中的 `skills/` 保存源文件；客户端从自己的发现目录加载技能。以下路径于 2026-10-29 依据表中的公开源码和官方文档核对，已安装版本可能不同，安装后仍需确认客户端能实际发现技能。

| 客户端范围 | 用户级目录 | 项目级目录 | 核实来源 |
| --- | --- | --- | --- |
| 本地 Codex | `~/.agents/skills/<name>/SKILL.md` | 项目范围内的 `.agents/skills/<name>/SKILL.md` | [OpenAI 第一方源码](https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/host_roots.rs) |
| 本地 Claude Code | `~/.claude/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` | [Claude Code 官方文档](https://code.claude.com/docs/en/skills) |

用户级安装适用于多个项目；项目级安装只服务对应项目。Codex 的旧 `$CODEX_HOME/skills` 在核实的源码中仍为兼容保留路径，新安装使用上表位置。

Claude.ai、Cowork 和云端会话有各自的配置方式，不读取上述本机用户目录时，需要按对应环境的文档安装。

## 校验并复制

先从仓库根目录检查技能：

```bash
python scripts/validate.py --path skills/maintain-docs
```

安装到本地 Codex 用户目录：

```bash
python - <<'PY'
from pathlib import Path
from shutil import copytree

source = Path("skills/maintain-docs")
destination = Path.home() / ".agents" / "skills" / source.name
copytree(source, destination)
print(f"Installed {source.name} to {destination}")
PY
```

目标已存在时，`copytree` 会报错；更新已有安装见下节。安装到本地 Claude Code 时，将代码中的 `.agents` 改成 `.claude`；项目级安装则将目标改为相应项目下的发现目录。

复制整个技能文件夹，包含其相对路径资源。仓库文档、模板和评测目录无需安装。

## 确认可用

按客户端要求刷新或新建会话，确认它能发现该技能，再用真实请求检查技能选择记录和任务结果。客户端版本可能与引用源码不同，以实际发现和执行结果为准；记录方式见 [评测指南](../evals/README.md)。

## 更新与卸载

复制安装不会自动同步仓库修改。更新前比较源目录与已安装目录，保留安装处的独有修改，校验和评测源文件后再替换对应技能。卸载时仅移除该技能目录，不清理客户端中的其他技能。

## 客户端扩展

`agents/openai.yaml`、Claude 专用字段和权限配置各有语义，需要时按对应客户端版本添加。插件市场、连接器或 hooks 等能力可另加平台包装，核心技能仍保留在 `skills/`。分发方式的设计依据见 [设计说明](design.md)，客户端行为以适用版本的公开文档和实现为准。
