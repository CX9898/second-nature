# 评测指南

技能评测回答两个问题：请求是否会选中合适的技能，选中后能否改善任务结果。这里采用手工案例与运行记录；`scripts/validate.py` 检查案例定义和资源路径，不运行模型或执行被测任务。

以下路径与命令均相对于仓库根目录。编写流程见 [编写指南](../docs/authoring.md)。

## 目录职责

每个技能的案例及其输入放在同名目录中，按需添加资源：

```text
evals/
├── README.md
└── <skill-name>/
    ├── cases.yaml           请求与行为判据
    ├── inputs/              独立输入文件（可选）
    └── fixtures/            完整的样本项目（可选）
        └── <project>/
```

`cases.yaml`、`inputs/` 和 `fixtures/` 是需要提交的评测源文件；对话记录、工作区副本、截图、报告及其他运行产物默认保存在 `.local/evals/`。其他输出位置也必须被 Git 忽略，例如兼容目录 `tmp/` 或 `evals/runs/`。正式文档只引用随库的案例与判据，不链接本地产物。

输入和 fixture 可以故意包含错误描述、失效链接或不应执行的命令。它们是被测材料，不是本仓库的使用说明；日常文档准确性、链接有效性和文字整理检查应排除 `evals/*/inputs/` 与 `evals/*/fixtures/`。可以检查这些材料是否存在、是否被案例正确引用，但不要为通过日常检查而修复其中的故意缺陷。

## 准备案例

为新技能复制 [案例模板](../templates/eval-case.yaml)：

```bash
mkdir -p evals/review-experiment
cp -i templates/eval-case.yaml evals/review-experiment/cases.yaml
```

已有案例时直接修改对应文件。将顶层 `skill: skill-name` 改为实际技能名，替换全部 `TODO`，并按需要添加输入文件和执行环境说明。

| 字段 | 用途 |
| --- | --- |
| `skill` | 被评测的技能名，与目录名一致 |
| `fixture` | 可选；完整样本项目的源目录，对该文件内的案例提供共同初始状态 |
| `cases[].id` | 文件内唯一的案例标识 |
| `request` | 一条真实用户请求 |
| `input_files` | 可选；本案例所需的源文件列表，可以指向独立输入或 fixture 内文件 |
| `expected_trigger` | 技能可被自动发现时，是否预期选中它 |
| `expected_behaviors` | 该请求应满足的可观察结果 |
| `forbidden_behaviors` | 应避免的具体错误或副作用 |

至少覆盖一条应触发请求、一条相近但不应触发的请求，以及一个重要边界场景。判据关注任务结果，不固定模型的措辞、标题或实现细节。

`fixture` 和 `input_files` 都从仓库根目录解析，不相对于 `cases.yaml`。例如 [maintain-docs 案例](maintain-docs/cases.yaml) 的 `fixture: evals/maintain-docs/fixtures/project` 指向只读的源项目；它不是实际执行时允许修改的工作区。

## 准备独立工作区

每个案例、基线组、实验组和重复运行都必须从源 fixture 重新准备，建议使用独立目录：

```text
.local/evals/<skill-name>/<run-id>/<case-id>/<group>/
```

`run-id` 标识一次运行或重复实验，`group` 可用 `baseline`、`with-skill`；自动触发与显式调用分别使用独立组或运行。不要复用先前已被修改的副本，也不要跨案例共享可写工作区。

以下示例手工复制一个案例的基线工作区，不执行 fixture 中的程序；命令在仓库根目录运行，`copytree` 会拒绝已经存在的目标目录：

```bash
python - <<'PY'
from shutil import copytree

copytree(
    "evals/maintain-docs/fixtures/project",
    ".local/evals/maintain-docs/trial-001/repair-documentation-and-generator-source/baseline",
)
PY
```

使用其他输出位置时，复制前通过 `git check-ignore -v -- <目标路径>` 确认它被忽略；目标不能位于源 fixture 内部。

将被测对话的工作目录设为副本根目录。请求中 `README.md`、`docs/quickstart.md` 等操作目标相对于副本项目根目录解析；YAML 中的仓库源路径只用于取材，不作为修改目标。

fixture 内的输入随项目复制；独立输入可以作为只读附件提供。需要改写时，先复制到工作区内的 `case-inputs/`，避免同名覆盖，并记录源路径与目标路径。没有 fixture 的案例可创建空工作区后复制所需输入。向被测对话提供副本路径，不提供源文件作为修改目标。

基线、实验和重复运行必须使用相同的原始输入和环境。保持提交的源 fixture 与输入只读，所有输出和允许的修改发生在已被 Git 忽略的副本中；需要升级样本时，作为单独的案例维护变更处理。

## 分开检查触发与执行

### 自动触发

让技能处于可发现状态，在新对话中提交原始请求，不在请求中指定技能名。根据客户端提供的实际选择记录，与 `expected_trigger` 比较；拿不到记录时，将触发结果记为“无法判断”。任务完成本身不能证明技能是否被选择。

显式指定技能可以检查执行能力，但不能证明它会在普通请求中自动触发。

### 任务效果

固定模型、工具权限、输入文件和初始工作区，分别运行不加载目标技能的基线组与加载目标技能的实验组。每次使用新对话，比较最终产物、测试结果和实际操作。

基线组用于比较任务效果，不依据 `expected_trigger` 判定失败。实验组需要实际确认技能已加载；如果自动触发没有选中，可另跑一次显式调用并单独记录。出现输出波动时重复运行，避免凭单次结果判断。

## 记录与迭代

本地运行记录和产物默认放在 `.local/evals/<skill-name>/<run-id>/`，自定义输出时一并保存在该忽略目录中；案例源文件保留在 `evals/<skill-name>/`。运行记录可以注明本地产物路径，但不得从提交的文档链接这些产物。建议记录：

```text
日期 / 客户端及版本 / 模型：
仓库版本或工作区状态：
案例 ID / 基线组或实验组 / 自动选择或显式调用：
实际技能选择记录 / 是否确认加载：
预期行为 / 实际行为：
触发结论 / 任务效果结论（通过、失败或无法判断）：
证据路径 / 下一次修改：
```

修改技能后重跑相关案例，保留暴露问题的请求及判据；只有观察到行为问题时才增加对应规则。

## 与自动评测工具的关系

本仓库的 YAML 是手工约定。[Agent Skills 官方评测指南](https://agentskills.io/skill-creation/evaluating-skills) 推荐 skill 内的 `evals/evals.json`。接入采用该约定的工具时，需要转换格式或适配路径；这里的 YAML 不能直接当作兼容输入。
