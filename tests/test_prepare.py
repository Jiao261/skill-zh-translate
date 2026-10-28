# -*- coding: utf-8 -*-
"""prepare.py 的备份与分类测试。"""
import zipfile

from conftest import EN_SKILL, run_cli, write_skill


def test_backup_created_and_identical(en_skill, backup_dir):
    """备份必须存在，且内容与原文逐字节一致。"""
    assert backup_dir.is_dir()
    for f in en_skill.rglob("*"):
        if f.is_file():
            rel = f.relative_to(en_skill)
            assert (backup_dir / rel).read_bytes() == f.read_bytes()


def test_classifies_text_and_code(en_skill, tmp_path):
    """SKILL.md 归入 translate，.py 归入 code。"""
    res = run_cli("prepare.py", en_skill, "--backup-dir", tmp_path / "bak")
    assert res.returncode == 0
    assert "待翻译 (translate)" in res.stdout
    assert "SKILL.md" in res.stdout
    assert "代码·默认不动 (code)" in res.stdout
    assert "scripts/run.py" in res.stdout


def test_detects_already_chinese(tmp_path):
    """已是中文的技能应被标记为可跳过，避免重复劳动。"""
    from conftest import ZH_SKILL

    d = write_skill(tmp_path / "src", skill_md=ZH_SKILL)
    res = run_cli("prepare.py", d, "--backup-dir", tmp_path / "bak")
    assert "疑似已是中文" in res.stdout


def test_skill_md_first_in_order(en_skill, tmp_path):
    """翻译顺序里 SKILL.md 必须排第一。"""
    (en_skill / "references").mkdir()
    (en_skill / "references" / "extra.md").write_text("Some extra doc.\n", encoding="utf-8")

    res = run_cli("prepare.py", en_skill, "--backup-dir", tmp_path / "bak")
    order_block = res.stdout.split("翻译顺序建议：")[1]
    first = order_block.strip().splitlines()[0]
    assert "SKILL.md" in first


def test_skips_git_directory(en_skill, tmp_path):
    """.git 里的文件不参与清点，也不进备份。"""
    (en_skill / ".git").mkdir()
    (en_skill / ".git" / "config").write_text("x", encoding="utf-8")

    res = run_cli("prepare.py", en_skill, "--backup-dir", tmp_path / "bak")
    assert res.returncode == 0
    bak = next((tmp_path / "bak").glob("*/demo-skill"))
    assert not (bak / ".git").exists()


def test_zip_input_extracted(tmp_path):
    """支持直接传 zip 包。"""
    src = write_skill(tmp_path / "pack")
    zpath = tmp_path / "demo.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for f in src.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(tmp_path / "pack"))

    res = run_cli("prepare.py", zpath, "--backup-dir", tmp_path / "bak")
    assert res.returncode == 0
    assert "已解压到" in res.stdout


def test_no_backup_flag(en_skill, tmp_path):
    """--no-backup 时不生成备份目录。"""
    res = run_cli("prepare.py", en_skill, "--backup-dir", tmp_path / "bak", "--no-backup")
    assert res.returncode == 0
    assert "已跳过备份" in res.stdout
    assert not (tmp_path / "bak").exists()
