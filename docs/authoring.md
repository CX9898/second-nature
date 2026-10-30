# 编写指南

本文覆盖从环境准备、选题到收录的流程。以下命令均在仓库根目录执行。

## 环境准备

维护工具需要 Python 3.10 或更高版本：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate.py
```

后续工作在同一环境中继续；新开终端时重新激活 `.venv` 即可。完整目录与上库边界见 [仓库结构与约定](design.md)。

## 先确定一个具体任务

从你经常重复纠正 AI 的任务开始，例如某种代码审查、实验报告或排障流程。先写几条真实请求和预期产物，明确技能补充的判断依据、领域知识或操作方法。

如果一段指令对几乎所有任务都适用，更适合个人设置；只适用于某个项目的构建和测试约定，通常放该项目的 `AGENTS.md`。完整边界见 [设计说明](design.md#指令放在哪里)。

## 创建草稿

已有技能可以直接进入 [编写入口](#编写入口)，无需再次运行创建命令。

在仓库根目录运行：

```bash
python scripts/new_skill.py review-experiment
```

如果一开始就需要辅助文件，可以改用下面的命令。两个命令二选一，创建器不会覆盖已有目录：

```bash
python scripts/new_skill.py review-experiment --resources references,scripts
```

创建结果位于 `skills/review-experiment/`，包含入口和从根目录复制的 `LICENSE`。入口模板来自 [SKILL.md.template](../templates/skill/SKILL.md.template)，其中的 `TODO:` 描述会使校验失败，提醒你先完成内容。需要后补资源时，直接在已有技能内新增相应文件即可。

## 编写入口

`SKILL.md` 的 YAML frontmatter 至少包含：

```yaml
---
name: review-experiment
description: 审查机器学习实验报告中的对照设置、指标口径和结论证据。在用户请求审查实验报告时使用。
---
```

`name` 与目录名一致，用小写英文字母、数字和连字符，最多 64 字符，不使用首尾或连续连字符。描述写清能力和触发条件，避免“帮助处理所有开发问题”这样的宽泛表述。

正文写任务目标、关键判断和必要步骤。不要重复模型已掌握的基础知识，也不要把某一次失败扩展成对所有任务的强制流程。输出格式只有在用户或任务有明确要求时才固定。

## 按需增加资源

| 路径 | 放什么 | 何时需要 |
| --- | --- | --- |
| `references/` | 领域规则、格式约定、较长示例 | 部分任务才需要读取的细节 |
| `scripts/` | 可执行、可复现的辅助程序 | 重复操作需要确定性执行 |
| `assets/` | 供产物使用的模板、图片等 | 生成结果确实需要素材 |
| `agents/openai.yaml` | Codex UI 信息、策略或依赖声明 | 当前客户端有明确需求时，按官方格式添加 |

在 `SKILL.md` 中链接资源并说明什么时候读取。使用相对路径，确保技能单独复制后仍可用；不要依赖仓库外的绝对路径或另一个未声明安装的技能。

## 基础校验

```bash
python scripts/validate.py
```

默认检查全部技能的基础格式、公开文档的本地链接，以及 `evals/<skill-name>/cases.yaml` 的结构和资源路径；CI 运行同一条命令。只检查一个技能的格式时：

```bash
python scripts/validate.py --path skills/review-experiment
```

技能格式检查覆盖 UTF-8、YAML、必需字段、命名与目录一致性、描述长度、`TODO:` 描述前缀和非空正文。全仓检查还会拒绝指向不存在、被忽略或仓库外本地文件的文档链接，核对案例所属技能、案例 ID、请求与触发布尔值，以及 fixture 和输入路径。

故意包含文档错误的评测 fixture、输入和未完成模板不参加普通文档链接检查。校验不验证远端服务、页面锚点、所有客户端专用字段或模型效果，也不会判断正文模板内容是否已写完。

修改维护程序时，另运行工具测试：

```bash
python -m unittest discover -s tests
```

## 效果评测

按 [评测指南](../evals/README.md) 在 `evals/<skill-name>/cases.yaml` 创建真实请求，将配套项目和额外输入放在同目录的 `fixtures/`、`inputs/`。手工复制到独立工作区，优先放在 `.local/evals/`；使用其他路径前确认它被 Git 忽略，不在原样本上执行修改任务。

比较加载技能前后的行为，先检查是否正确触发，再检查最终产物和实际操作。

每次迭代围绕一个可观察的问题：触发范围是否正确、关键判断是否遗漏、产物是否达标、是否执行了未要求的动作。脚本则实际运行验证，避免用测试仅检查指令中是否存在某句话。

## 收录与维护

完成内容、基础校验和行为评测后，技能可直接通过 [skills/](../skills/) 浏览，无需在根 README 登记名称或更新技能数量。名称与适用任务由技能自己的 frontmatter 描述；安装步骤见 [使用指南](usage.md)。

后续用 Git 历史记录迭代；修改技能后重跑相关案例。借鉴第三方内容和公开分享前，按 [许可证约定](design.md#许可证) 检查授权与来源。

调研过程与一次性草稿优先写入 `.local/research/` 或 `.local/tmp/`，调用工具或委派任务时明确传入输出位置。工具若仍写入 `docs/research/`、`tmp/` 等兼容目录，先用 `git check-ignore -v -- <路径>` 确认忽略规则生效。

需要读者长期掌握的结论，应写入随库文档并附公开来源；公开文档不链接任何被忽略的本地材料，具体目录是否叫 `.local/` 不影响这一要求。输出目录的分类与保底规则见 [仓库结构与约定](design.md#哪些内容随库发布)。
