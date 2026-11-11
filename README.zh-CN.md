# forgejo-cli-skill

[English](README.md) | **简体中文**

遵循 [Agent Skills 开放规范](https://agentskills.io/specification) 的 skill，帮助编码 agent 正确、安全地使用 [`fj`（forgejo-cli）](https://codeberg.org/forgejo-contrib/forgejo-cli) 操作 Forgejo 和 Codeberg。这是独立的 skill 项目，不是上游 CLI，也不是凭据管理器。

**分发：**可从 Git 安装，或下载 [GitHub Releases](https://github.com/longredzhong/forgejo-cli-skill/releases) 中列出的版本。npm 发布是独立流程，目前尚未执行。skill 自带运行环境 `compatibility` 和字符串映射 `metadata`，记录自身版本、仓库、上游项目及已测试 CLI 版本；测试确保 skill 版本与 `package.json` 一致。

## 安装

先单独安装上游 `forgejo-cli`，运行 `fj version` 检查。方法见[上游安装文档](https://codeberg.org/forgejo-contrib/forgejo-cli/wiki/Installation)。skill 安装器不会安装 fj、登录账号或执行远端操作。

### 使用 Skills CLI 从 Git 安装

```bash
npx skills add https://github.com/longredzhong/forgejo-cli-skill --skill forgejo-cli
```

Skills CLI 会发现 `skills/forgejo-cli/SKILL.md`，并让你选择 agent 与安装范围。这条路径使用 npm 上的 **Skills CLI**，但**不要求本项目发布到 npm**。需要可复现安装时，应核实并固定安装器与源码版本。

### 从 release ZIP 安装

release 发布后，从附件下载 `forgejo-cli-skill-VERSION.zip` 和 `SHA256SUMS`。在新的下载目录验证校验和，再解压到 agent 的 skills 目录。ZIP 只有一个顶层 `forgejo-cli/`，其内含 `SKILL.md` 与 `references/`；不额外套 `skills/`，也不包含仓库测试或凭据。校验和可以检查损坏，但不能证明不可信发布源的真实性。

### 通过 npm/npx 安装（npm 发布之后）

需要 Node.js **22.14+**。在 `0.1.0` 确实发布后，可以运行：

```bash
npx forgejo-cli-skill@0.1.0 install --dir .agents/skills --dry-run
npx forgejo-cli-skill@0.1.0 install --dir .agents/skills
```

`--dir` 指向 **skills 的父目录**，安装器会在其中创建 `forgejo-cli/`。请选择 agent 支持的路径。若 agent 支持用户级路径，可用 `--dir ~/.agents/skills`（由 shell 展开），或使用 agent 专有的父目录。目标处已有文件、目录或符号链接都会拒绝安装，没有覆盖/force 模式。升级前请自行检查并备份旧 skill，再选择不存在的目标安装。

现在即可本地测试实现，无需先发布 npm：

```bash
node bin/forgejo-cli-skill.mjs install --dir /tmp/my-agent-skills --dry-run
```

也可以手动复制整个 `skills/forgejo-cli/`，不要只复制 `SKILL.md`。最终目录名保持为 `forgejo-cli`。

## 使用

向 agent 提出明确的 Forgejo 任务，例如：

- “查看这个 Codeberg 仓库中所有状态的 timeout 相关 issue。”
- “阅读这个 Forgejo PR 的 diff、评论和 CI 状态，不要发布内容。”
- “按仓库要求的模板和准备好的正文文件创建 issue。”
- “为这个分支创建指定 base/head 的 PR，不要合并。”

skill 指令用英文编写以方便跨 agent 复用。入口包含流程和关键陷阱，参考文档按需加载。写操作仍需用户授权。

## 覆盖范围与安全

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](skills/forgejo-cli/SKILL.md) | 工作流程、明确目标、非交互默认值与安全边界 |
| [认证与目标选择](skills/forgejo-cli/references/auth-and-targeting.md) | 主机、登录、remotes、仓库与对象 ID |
| [Issues](skills/forgejo-cli/references/issues.md) | 模板、正文、标签、里程碑、依赖 |
| [Pull requests](skills/forgejo-cli/references/pull-requests.md) | fork/AGit、reviews、checkout、CI、merge |
| [仓库与 wiki](skills/forgejo-cli/references/repositories.md) | 创建、迁移、units、标签、wiki |
| [Actions 与 releases](skills/forgejo-cli/references/actions-and-releases.md) | 变量/secrets、dispatch、里程碑、tags、release、assets |
| [组织与用户](skills/forgejo-cli/references/organizations-and-users.md) | teams、权限、个人资料、公钥 |
| [故障处理](skills/forgejo-cli/references/troubleshooting.md) | 参数/版本差异、交互输入、输出、重试 |

skill 不读取 `keys.json`，不虚构通用 `fj api`/JSON 接口，不把 `pr status --wait` 的零退出码当作 CI 通过，也不会绕过保护。npm 安装器只复制随包提供的 Markdown：无第三方运行时依赖、无安装生命周期钩子、无网络调用、不自动检测 agent。**只有 npm 安装需要 Node；安装后使用 skill 不需要 Node 或 Python。**

命令示例已按 `fj v0.8.0-dev` 校对，不保证所有历史/未来版本。执行时以安装版本的 help 为准。来源见[依据与维护说明](https://github.com/longredzhong/forgejo-cli-skill/blob/main/docs/sources.md)。

## 开发与验证

仓库/ZIP 检查需要 Python **3.9+**；安装器/包检查另需 Node.js **22.14+** 与 npm。可选的 fj help 检查不会访问远端 API。

```bash
npm ci --ignore-scripts
npm test
python3 -I -m unittest discover -s tests -v
FJ_SKILL_CLI_CHECK=1 python3 -I -m unittest discover -s tests -v
```

Python 测试检查 skill 结构、链接、评估场景结构、ZIP 可复现内容与校验和，以及离线 npm tarball/npx 安装。可选 fj 检查在隔离的 HOME/XDG 目录对示例追加 `--help`，不会执行其中的写操作。Node 测试覆盖安装、dry-run、冲突、非法参数、符号链接与打包边界。

已安装官方验证器时，可进一步校验完整标准格式：

```bash
skills-ref validate skills/forgejo-cli
```

[13 个行为场景](https://github.com/longredzhong/forgejo-cli-skill/blob/main/evals/scenarios.json) 需在可控的 agent 环境中运行。结构/help 测试不代表真实 agent 行为或服务端兼容性验证。

## 构建与发布

```bash
python3 -I scripts/build_release.py --output dist
npm pack --ignore-scripts --pack-destination dist
```

ZIP 构建拒绝覆盖已有输出，重复构建请用新目录。版本统一来自 `package.json`。推送与版本一致的稳定 `vVERSION` tag 后，会触发测试、ZIP 构建并生成附带 ZIP/校验和的 draft GitHub Release。流程不会创建缺失 tag、覆盖 release 附件或自动发布 npm。

draft 转正、精确 tag 验证、npm 调研、首次发布前置条件与可选的手动 OIDC 发布流程，见[分发与发布说明](https://github.com/longredzhong/forgejo-cli-skill/blob/main/docs/distribution.md)。当前 npm 元数据为 `UNLICENSED`：公开分发前，维护者需明确许可证并确认包名所有权。本项目不会自动继承上游许可证。
