# -*- coding: utf-8 -*-
"""命令行冒烟测试：保证脚本在任何区域设置下都能正常启动。

Windows 默认控制台是 cp1252/cp936，中文帮助文本会触发 UnicodeEncodeError。
这个文件专门锁住这个回归——CI 上就是这样抓到问题的。
"""
import pytest

SCRIPTS = ("scan.py", "prepare.py", "verify.py")


@pytest.mark.parametrize("script", SCRIPTS)
def test_help_exits_zero(script):
    """--help 必须正常退出，而不是被编码问题打断。"""
    from conftest import run_cli

    res = run_cli(script, "--help")
    assert res.returncode == 0, res.stderr
    assert "usage" in res.stdout.lower()


@pytest.mark.parametrize("script", SCRIPTS)
def test_help_survives_cp1252_console(script):
    """模拟 Windows 默认 cp1252 控制台：脚本内部应强制切到 UTF-8。"""
    from conftest import run_cli

    res = run_cli(
        script, "--help",
        env={"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"},
    )
    assert res.returncode == 0, res.stderr
    assert "UnicodeEncodeError" not in res.stderr


@pytest.mark.parametrize("script", SCRIPTS)
def test_help_contains_chinese(script):
    """帮助文本里应当有中文描述，说明本地化没有丢失。"""
    from conftest import run_cli

    res = run_cli(script, "--help")
    assert any("\u4e00" <= ch <= "\u9fff" for ch in res.stdout), "帮助文本里没有中文"
