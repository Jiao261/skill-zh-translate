# -*- coding: utf-8 -*-
"""verify.py 的校验能力测试：既要放行正确译文，也要真的抓住破坏。"""
from conftest import ZH_SKILL, run_cli


def test_good_translation_passes(translated_skill, backup_dir):
    """结构完整的正确译文应当 0 ERROR 且退出码 0。"""
    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert res.returncode == 0, res.stdout
    assert "ERROR 0" in res.stdout
    assert "通过" in res.stdout


def test_catches_frontmatter_name_change(translated_skill, backup_dir):
    """frontmatter 的 name 被翻译/改名必须报 ERROR —— 否则技能调用会断。"""
    broken = ZH_SKILL.replace("name: demo-skill", "name: demo-skill-zh")
    (translated_skill / "SKILL.md").write_text(broken, encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert res.returncode == 1
    assert "name 被改动" in res.stdout


def test_catches_code_block_tamper(translated_skill, backup_dir):
    """围栏代码块内容被改动（run.py → runner.py）必须报 ERROR。"""
    broken = ZH_SKILL.replace("scripts/run.py", "scripts/runner.py")
    (translated_skill / "SKILL.md").write_text(broken, encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert res.returncode == 1
    assert "代码块内容" in res.stdout


def test_catches_lost_link(translated_skill, backup_dir):
    """链接目标丢失应报 WARN（可能是合理改动，但不能静默）。"""
    broken = ZH_SKILL.replace("，详见 [文档](https://example.com/docs)。", "。")
    (translated_skill / "SKILL.md").write_text(broken, encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert "链接目标 丢失" in res.stdout


def test_catches_lost_inline_code(translated_skill, backup_dir):
    """行内代码被译成中文应被发现（命令不能翻译）。"""
    broken = ZH_SKILL.replace("`run.py --verbose`", "`运行脚本`")
    (translated_skill / "SKILL.md").write_text(broken, encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert "行内代码" in res.stdout


def test_catches_unpaired_fence(translated_skill, backup_dir):
    """代码块 ``` 未配对说明译文被截断，必须报 ERROR。"""
    broken = ZH_SKILL.replace("```\n\n行内示例", "\n行内示例")
    (translated_skill / "SKILL.md").write_text(broken, encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert res.returncode == 1
    assert "未配对" in res.stdout


def test_catches_lost_frontmatter(translated_skill, backup_dir):
    """frontmatter 整块丢失必须报 ERROR。"""
    broken = ZH_SKILL.split("---", 2)[2]
    (translated_skill / "SKILL.md").write_text(broken, encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert res.returncode == 1
    assert "frontmatter 丢失" in res.stdout


def test_warns_when_code_file_modified(translated_skill, backup_dir):
    """代码文件被改动应给出 WARN（规则要求默认不动）。"""
    (translated_skill / "scripts" / "run.py").write_text(
        "def main(payload):\n    return payload\n", encoding="utf-8")

    res = run_cli("verify.py", translated_skill, "--backup", backup_dir)
    assert "代码文件内容被修改" in res.stdout


def test_missing_backup_dir_errors(translated_skill, tmp_path):
    """备份目录不存在时直接报错，不做无意义比对。"""
    res = run_cli("verify.py", translated_skill, "--backup", tmp_path / "nope")
    assert res.returncode == 1
    assert "备份目录不存在" in res.stdout


def test_resolves_skill_by_name(translated_skill, backup_dir, tmp_path):
    """传入技能名（而非路径）也应能解析到目录。"""
    fake_home = tmp_path / "home"
    skills = fake_home / ".workbuddy-ai" / "skills"
    skills.mkdir(parents=True)
    target = skills / translated_skill.name
    target.mkdir()
    for f in translated_skill.rglob("*"):
        if f.is_file():
            rel = f.relative_to(translated_skill)
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            (target / rel).write_bytes(f.read_bytes())

    res = run_cli("verify.py", translated_skill.name, "--backup", backup_dir,
                  env={"SKILL_ZH_ROOTS": str(skills)})
    assert res.returncode == 0, res.stdout
    assert "ERROR 0" in res.stdout


def test_unknown_skill_name_reports_roots(tmp_path):
    """找不到技能时，应把已发现的技能目录列出来，方便用户排查。"""
    res = run_cli("verify.py", "no-such-skill-xyz", "--backup", tmp_path,
                  env={"SKILL_ZH_ROOTS": str(tmp_path)})
    assert res.returncode == 1
    assert "已发现的技能目录" in res.stdout
