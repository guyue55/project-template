# Project Template

精简、与应用语言无关的 GitHub 开发仓库模板：让人和 AI 快速了解边界，提交前有检查，发布后有可核验的来源。不附带业务框架、数据库或容器，不用一套占位应用限制后续选型。

## 创建新项目

在 GitHub 点击 **Use this template**，或使用本地生成器（Python 3.12+、Git）：

```sh
python3 scripts/new_project.py --name my-project --owner your-account --output ../my-project
```

生成器只导出已提交且干净的 HEAD，目标必须不存在，不带 Git 历史、凭证、运行状态或本机环境；不会自动初始化 Git、推送或发布。生成后按实际需求修改 README、AGENTS、许可与真实代码门禁，再初始化独立 Git 历史。GitHub 生成方式不会自动改名文件中的 project.toml，请同步其中 owner/name。

## 已包含

- AGENTS.md：AI 工作入口、中文注释／提交约定、权限与泄密红线。
- CONTRIBUTING／SECURITY／行为准则、Issue 表单、PR 模板。
- 仓库卫生和提交检查、可选本地 hooks；跨平台 CI、固定 Action SHA、历史秘密扫描。
- project.toml 集中仓库标识，VERSION 与变更记录；源码候选、来源清单、SHA256SUMS、离线发布复核。
- Python 标准库验证和生成工具的正负测试，不引入通用大框架。

## 本仓库检查

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Windows 可用 `py -3`。检查工具需要 Python 3.12+，不代表应用必须用 Python。代码格式、类型检查和真实业务测试要随选定技术栈添加，治理检查不能替代它们。

[贡献与提交](CONTRIBUTING.md) · [AI 约定](AGENTS.md) · [安全](SECURITY.md) · [操作与发版](docs/OPERATIONS.md) · [研究依据](docs/RESEARCH.md)

## 许可与边界

Apache-2.0，保留适用 LICENSE／NOTICE 与来源。无需把所有文件复制为每种 AI 工具的专有配置；按宿主支持读取 AGENTS.md。模板文件不会自动设置远程分支保护、私密报告或部署环境，创建仓库后需另行核验。
