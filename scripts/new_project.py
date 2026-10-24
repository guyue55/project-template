"""从干净已提交模板生成独立源码，不初始化Git或修改远端。"""

import argparse
import io
import json
import re
import zipfile
from pathlib import Path

from check import ROOT, git


def generate(output, name, owner):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("项目名须为小写kebab-case")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", owner):
        raise ValueError("GitHub所有者格式无效")
    if output.is_symlink():
        raise ValueError("目标不能是软链")
    output = output.resolve()
    if output.exists() or output.is_symlink() or output.is_relative_to(ROOT.resolve()):
        raise ValueError("目标须为仓库外不存在的新目录")
    if git("status", "--porcelain").strip():
        raise ValueError("模板须已提交且工作区干净")
    raw = git("archive", "--format=zip", "HEAD")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for item in archive.infolist():
            path = Path(item.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in item.filename
                or (item.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ValueError("源归档含危险成员")
        output.mkdir(parents=True, exist_ok=False)
        archive.extractall(output)
        for item in archive.infolist():
            target = output / item.filename
            if not item.is_dir() and (item.external_attr >> 16) & 0o111:
                target.chmod(0o755)
    # 仓库标识与本项目状态更新；不修改上游许可与来源，也不做全树品牌替换。
    (output / "project.toml").write_text(
        f'[project]\nname = {json.dumps(name)}\nowner = {json.dumps(owner)}\nkind = "template"\ndescription = "新项目，待按实际需求完善"\n'
    )
    (output / "VERSION").write_text("0.1.0\n")
    (output / "CHANGELOG.md").write_text("# 变更记录\n\n## 0.1.0\n\n项目初始化，尚未发布。\n")
    (output / "releases/v1.0.0.md").unlink(missing_ok=True)
    (output / "releases/v0.1.0.md").write_text(
        f"# {name} v0.1.0\n\n项目初始化。发布前填写真实能力、兼容、验证和限制，不继承模板验收。\n"
    )
    (output / "README.md").write_text(
        f"# {name}\n\n待按实际需求完善定位、安装、使用和测试命令。当前仅含项目治理模板，不代表应用已经实现。\n\n"
        "先阅读 [AGENTS.md](AGENTS.md)、[贡献规范](CONTRIBUTING.md)、[安全](SECURITY.md) 与 [发版手册](docs/OPERATIONS.md)。\n\n"
        "仓库检查：`python3 scripts/check.py`。按应用技术栈补充真实测试与CI门禁；初始化Git前检查公开边界与许可。\n"
    )
    print("PROJECT_GENERATED", output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--owner", required=True)
    args = parser.parse_args()
    generate(args.output, args.name, args.owner)


if __name__ == "__main__":
    main()
