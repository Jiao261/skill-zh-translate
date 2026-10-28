# -*- coding: utf-8 -*-
"""scan.py 的扫描与排序测试。"""
from conftest import run_cli, write_skill


def _make(root, name, body):
    d = write_skill(root, skill_md=body, name=name)
    return d


def test_sorted_by_size_ascending(tmp_path):
    """默认视图必须按文本量升序，保证「从上往下做」始终收益最快。"""
    root = tmp_path / "skills"
    root.mkdir()
    # 故意用体积递减的顺序创建，检验排序是否真的生效
    _make(root, "big", "---\nname: big\n---\n\n" + "Large body text here.\n" * 80)
    _make(root, "mid", "---\nname: mid\n---\n\n" + "Mid body text here.\n" * 20)
    _make(root, "tiny", "---\nname: tiny\n---\n\nSmall.\n")

    res = run_cli("scan.py", "--roots", root)
    assert res.returncode == 2, "存在待汉化技能时应返回退出码 2"
    rows = [ln for ln in res.stdout.splitlines() if ln.startswith(("big", "mid", "tiny"))]
    order = [r.split()[0] for r in rows]
    assert order == ["tiny", "mid", "big"], order


def test_exit_code_zero_when_all_done(tmp_path):
    """全部已汉化时退出码为 0，方便 CI 判断。"""
    root = tmp_path / "skills"
    root.mkdir()
    _make(root, "done-skill",
          "---\nname: done-skill\ndescription: 已经是中文的技能描述。\n---\n\n"
          "# 标题\n\n这里是完整的中文说明文字，用于让中文占比超过阈值，从而判定为已汉化。\n")

    res = run_cli("scan.py", "--roots", root)
    assert res.returncode == 0
    assert "全部已汉化" in res.stdout


def test_skips_nested_dirs_under_skill(tmp_path):
    """技能内部不再往下找，避免把 references 里的 md 误当成技能。"""
    root = tmp_path / "skills"
    root.mkdir()
    d = _make(root, "outer", "---\nname: outer\n---\n\nSome text.\n")
    nested = d / "vendor" / "inner"
    nested.mkdir(parents=True)
    (nested / "SKILL.md").write_text("---\nname: inner\n---\n\nNested.\n", encoding="utf-8")

    res = run_cli("scan.py", "--roots", root)
    assert "inner" not in res.stdout


def test_ignores_git_and_node_modules(tmp_path):
    """.git / node_modules 不参与扫描。"""
    root = tmp_path / "skills"
    root.mkdir()
    _make(root, "real", "---\nname: real\n---\n\nText.\n")
    junk = root / ".git" / "hooks"
    junk.mkdir(parents=True)
    (junk / "SKILL.md").write_text("---\nname: ghost\n---\n\nGhost.\n", encoding="utf-8")

    res = run_cli("scan.py", "--roots", root)
    assert "ghost" not in res.stdout


def test_env_var_overrides_roots(tmp_path):
    """SKILL_ZH_ROOTS 优先级最高，可指定任意目录。"""
    root = tmp_path / "custom"
    root.mkdir()
    _make(root, "via-env", "---\nname: via-env\n---\n\nText.\n")

    res = run_cli("scan.py", env={"SKILL_ZH_ROOTS": str(root)})
    assert "via-env" in res.stdout
    assert "自定义" in res.stdout


def test_json_report_written(tmp_path):
    """--json 输出的报告结构完整，供自动化消费。"""
    import json

    root = tmp_path / "skills"
    root.mkdir()
    _make(root, "a-skill", "---\nname: a-skill\n---\n\nText.\n")

    out = tmp_path / "report.json"
    res = run_cli("scan.py", "--roots", root, "--json", out)
    assert res.returncode == 2
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "todo" in data and "done" in data
    assert data["todo"][0]["name"] == "a-skill"
    assert "cjk_ratio" in data["todo"][0]
