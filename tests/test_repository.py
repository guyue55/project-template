"""治理工具的负向验证，不接触真实业务或全局Git配置。"""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check
import release


class RepositoryTests(unittest.TestCase):
    def test_chinese_commit_policy(self):
        self.assertTrue(check.message_valid("fix(parser): 拒绝重复键"))
        for text in ("fix: 错误", "fix(parser): english", "update", "fix(parser): "):
            self.assertFalse(check.message_valid(text))

    def test_pull_request_title_matches_squash_policy(self):
        check.check_event({})
        check.check_event({"pull_request": {"title": "fix(parser): 拒绝重复键"}})
        with self.assertRaises(ValueError):
            check.check_event({"pull_request": {"title": "English title"}})

    def test_current_repository(self):
        check.validate(dict(check.sources()))

    def test_missing_required_and_environment_file(self):
        files = dict(check.sources())
        with self.assertRaises(ValueError):
            check.validate({k: v for k, v in files.items() if k != "AGENTS.md"})
        with self.assertRaises(ValueError):
            check.validate(files | {".env": b"SYNTHETIC=true\n"})
        with self.assertRaises(ValueError):
            check.validate(files | {"credentials/data.txt": b"synthetic\n"})

    def test_staged_link_cannot_resolve_from_unstaged_file(self):
        files = dict(check.sources())
        files["README.md"] = b"[removed](docs/RESEARCH.md)\n"
        del files["docs/RESEARCH.md"]
        with self.assertRaises(ValueError):
            check.validate(files)

    def test_unsafe_archive_member(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.zip"
            for member in (
                "../escape",
                "/absolute",
                "C:/absolute",
                "C:relative",
                "project/NUL.txt",
                "project/credentials/data.txt",
            ):
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr(member, "synthetic")
                with self.assertRaises(ValueError):
                    release.archive_check(path)

    def test_release_digest_extra_asset_and_wrong_source(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            name, version, sha = "demo", "1.0.0", "a" * 40
            with zipfile.ZipFile(folder / "demo-source-1.0.0.zip", "w") as archive:
                archive.writestr("demo/LICENSE", "synthetic")
            (folder / "RELEASE_NOTES.md").write_text("synthetic\n")
            manifest = {
                "name": name,
                "version": version,
                "kind": "template",
                "source_commit": sha,
                "artifacts": {p.name: release.digest(p) for p in folder.iterdir()},
            }
            (folder / "release-manifest.json").write_text(json.dumps(manifest))
            (folder / "SHA256SUMS").write_text(
                "".join(f"{release.digest(p)}  {p.name}\n" for p in sorted(folder.iterdir()))
            )
            release.verify(folder, sha)
            with self.assertRaises(ValueError):
                release.verify(folder, "b" * 40)
            extra = folder / "unexpected.log"
            extra.write_text("synthetic")
            with self.assertRaises(ValueError):
                release.verify(folder, sha)
            extra.unlink()
            (folder / "RELEASE_NOTES.md").write_text("tampered")
            with self.assertRaises(ValueError):
                release.verify(folder, sha)


class GeneratorTests(unittest.TestCase):
    def test_clean_generation_rejects_dirty_existing_and_bad_identifiers(self):
        import shutil
        import subprocess

        import new_project

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            seed = base / "seed"
            shutil.copytree(
                check.ROOT,
                seed,
                ignore=shutil.ignore_patterns(
                    ".git", "runtime", "dist", "__pycache__", ".ruff_cache"
                ),
            )
            subprocess.run(
                ["git", "init", "-b", "main", str(seed)], check=True, capture_output=True
            )
            subprocess.run(["git", "add", "--all"], cwd=seed, check=True, capture_output=True)
            hooks = base / "empty-hooks"
            hooks.mkdir()
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Synthetic",
                    "-c",
                    "user.email=test@example.invalid",
                    "-c",
                    "commit.gpgsign=false",
                    "-c",
                    f"core.hooksPath={hooks}",
                    "commit",
                    "-m",
                    "chore(seed): 初始化合成模板",
                ],
                cwd=seed,
                check=True,
                capture_output=True,
            )
            with patch.object(check, "ROOT", seed), patch.object(new_project, "ROOT", seed):
                for name, owner in (("bad/name", "sample"), ("valid", "bad/owner")):
                    with self.assertRaises(ValueError):
                        new_project.generate(base / "bad", name, owner)
                # 未暂存的损坏文档不能污染暂存树检查。
                readme = seed / "README.md"
                original = readme.read_bytes()
                readme.write_text("[unstaged](missing.md)\n")
                check.validate(dict(check.sources(staged=True)))
                readme.write_bytes(original)
                target = base / "new"
                new_project.generate(target, "sample-project", "sample-owner")
                self.assertFalse((target / ".git").exists())
                self.assertEqual((target / "VERSION").read_text().strip(), "0.1.0")
                self.assertTrue((target / "releases/v0.1.0.md").exists())
                with patch.object(check, "ROOT", target):
                    check.validate(dict(check.sources()))
                with self.assertRaises(ValueError):
                    new_project.generate(target, "sample-project", "sample-owner")
                (seed / "uncommitted.txt").write_text("synthetic")
                with self.assertRaises(ValueError):
                    new_project.generate(base / "dirty", "sample-project", "sample-owner")


if __name__ == "__main__":
    unittest.main()
