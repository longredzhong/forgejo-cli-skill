# forgejo-cli-skill

让 agent 正确、安全地使用 [`fj`（forgejo-cli）](https://codeberg.org/forgejo-contrib/forgejo-cli)，而不是套用 GitHub CLI 的参数。

这是一个遵循 [Agent Skills 开放规范](https://agentskills.io/specification) 的 skill 仓库，不是 `fj` 的实现、封装器或凭据管理器，也不是上游官方项目。

## 安装

先安装上游 `forgejo-cli`，确保 `fj` 在 `PATH` 中。安装方法见[上游安装文档](https://codeberg.org/forgejo-contrib/forgejo-cli/wiki/Installation)。skill 本身不安装 CLI、不修改登录信息。

使用支持标准 skill 目录的 agent，将 **`skills/forgejo-cli/` 整个目录**复制到该 agent 的 skills 目录；最终目录名应保持为 `forgejo-cli`：

```text
<agent-skills-directory>/
└── forgejo-cli/
    ├── SKILL.md
    └── references/
        └── ...
```

例如，可按 agent 的文档选择项目级 `.agents/skills/forgejo-cli/` 或其他受支持的 skills 路径。不同 agent 的发现位置不同；不要把仓库根目录直接当作名为 `forgejo-cli` 的 skill，也不要只复制 `SKILL.md` 而丢掉参考文件。

若使用支持 Git 仓库发现的 skill 安装器，将当前仓库地址交给安装器并选择 `forgejo-cli` 即可。本仓库不要求特定的安装器或插件市场。

## 使用

让 agent 处理明确的 Forgejo 任务，例如：

- “查看这个 Codeberg 仓库中所有状态的 timeout 相关 issue。”
- “阅读这个 Forgejo PR 的 diff、评论和检查状态，先不要发布任何内容。”
- “按仓库模板创建 issue，正文从准备好的 Markdown 文件读取。”
- “为这个分支创建 PR，使用指定的 base/head，不要合并。”

skill 使用英文编写，以便跨 agent 复用；description 包含 Forgejo、Codeberg、fj、AGit 等触发词。主文件只保留工作流程与关键陷阱，参考文档按任务加载。

## 覆盖范围

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](skills/forgejo-cli/SKILL.md) | 入口、目标选择、安全边界、非交互默认值 |
| [auth-and-targeting.md](skills/forgejo-cli/references/auth-and-targeting.md) | 安装、认证、多实例、remotes、完整 ID |
| [issues.md](skills/forgejo-cli/references/issues.md) | 查询、模板、正文、标签、里程碑、依赖 |
| [pull-requests.md](skills/forgejo-cli/references/pull-requests.md) | 创建、fork/AGit、review、CI、checkout、merge |
| [repositories.md](skills/forgejo-cli/references/repositories.md) | 仓库、迁移、units、标签、wiki |
| [actions-and-releases.md](skills/forgejo-cli/references/actions-and-releases.md) | Actions、变量/secret 限制、milestone、tag、release、assets |
| [organizations-and-users.md](skills/forgejo-cli/references/organizations-and-users.md) | 组织、team、权限、用户、公钥 |
| [troubleshooting.md](skills/forgejo-cli/references/troubleshooting.md) | 参数差异、权限、交互阻塞、输出与重试 |

## 版本与依据

首版基于上游源码、wiki 和本机 `fj v0.8.0-dev` 的实际 help 校对。**不声明兼容所有历史/未来版本**：执行时仍应以安装版本的 `--help` 为准。源码依据与已核实差异见 [docs/sources.md](docs/sources.md)。

关键约束：

- 不读取或修改 `keys.json`，不携带任何真实主机、账号或 token。
- 不虚构通用 `fj api` / JSON 输出接口，不套用 `gh` 的 flags。
- 不把 `pr status --wait` 的零退出码当作 CI 成功。
- 不自动执行发布、合并、权限提升、删除或其他未授权写操作。
- 不包装 CLI，不引入运行时 Python/Node 依赖。

## 开发与验证

仓库检查仅需要 Python 3.9+；CLI 语法检查另外需要 `fj`。不读取真实凭据、不访问远端 API、不创建/修改远端资源。

```bash
python3 -I -m unittest discover -s tests -v
FJ_SKILL_CLI_CHECK=1 python3 -I -m unittest discover -s tests -v
```

第一条检查标准 frontmatter 的本仓库子集、目录命名、文档链接、参考文档可达性和评估样例。第二条额外从 skill 的 shell 示例提取命令，只追加 `--help` 检查安装版本是否接受这些参数；在临时 HOME/XDG 目录下运行，**不会执行示例中的写操作**。它不能验证服务端行为、正文模板解析、权限或实际副作用。

如已安装官方参考验证器，也可运行：

```bash
skills-ref validate skills/forgejo-cli
```

官方规范校验器负责完整格式验证；本仓库的零依赖测试不是它的完整替代品。行为评估场景在 [evals/scenarios.json](evals/scenarios.json)，需在可控的 agent 测试环境中评估；仓库测试仅检查场景结构，不声称已完成真实 agent 行为评估。

更新时：核对版本和源码 → 修正文档示例 → 运行两组测试 → 在用户授权的测试仓库做读回验证。不要将 help 解析通过等同于真实服务端兼容。
