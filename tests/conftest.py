# -*- coding: utf-8 -*-
"""pytest 公共夹具：构造最小可用的假技能，并提供 CLI 调用封装。"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# 一个结构完整的英文技能：frontmatter + 标题层级 + 围栏代码块 + 行内代码 + 链接
EN_SKILL = """---
name: demo-skill
description: A demo skill used to test the verification pipeline.
---

# Demo Skill

## Usage

Run the script below to generate a report. The script accepts a JSON payload on stdin
and prints a formatted summary to standard output for your review.

```bash
echo '{"x":1}' | python scripts/run.py
```

Inline example: `run.py --verbose` and see [docs](https://example.com/docs).

## Notes

This skill must not modify the code files, because the identifier names are used by
the runtime and any change will break the caller that depends on them.
"""

# 对应的正确译文：结构、代码块、行内代码、链接全部保持原样
ZH_SKILL = """---
name: demo-skill
description: 一个用于测试校验流程的演示技能。
---

# 演示技能

## 用法

运行下面的脚本即可生成报告。该脚本从标准输入接收 JSON 数据，并把格式化后的摘要打印到标准输出，供你查看。

```bash
echo '{"x":1}' | python scripts/run.py
```

行内示例：`run.py --verbose`，详见 [文档](https://example.com/docs)。

## 注意事项

本技能不得修改代码文件，因为其中的标识符名称由运行时使用，任何改动都会破坏依赖它的调用方。
"""

RUN_PY = """def main(payload):
    return {"ok": True, "payload": payload}
"""


def run_cli(script, *args, env=None, cwd=None):
    """以子进程方式调用脚本，返回 CompletedProcess（文本模式）。"""
    full_env = os.environ.copy()
    full_env["PYTHONIOENCODING"] = "utf-8"
    # 隔离外部 SKILL_ZH_ROOTS 影响
    full_env.pop("SKILL_ZH_ROOTS", None)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=full_env, cwd=str(cwd) if cwd else None,
    )


def write_skill(base: Path, skill_md: str = EN_SKILL, name: str = "demo-skill") -> Path:
    """在 base 下造一个技能目录。"""
    d = base / name
    (d / "scripts").mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (d / "scripts" / "run.py").write_text(RUN_PY, encoding="utf-8")
    return d


@pytest.fixture
def en_skill(tmp_path):
    """原始英文技能目录。"""
    return write_skill(tmp_path / "src")


@pytest.fixture
def backup_dir(en_skill, tmp_path):
    """跑 prepare.py 得到的备份目录。"""
    bak_root = tmp_path / "bak"
    res = run_cli("prepare.py", en_skill, "--backup-dir", bak_root)
    assert res.returncode == 0, res.stdout + res.stderr
    hits = list(bak_root.glob("*/" + en_skill.name))
    assert len(hits) == 1, "备份目录未按预期生成"
    return hits[0]


@pytest.fixture
def translated_skill(tmp_path, en_skill, backup_dir):
    """把英文技能就地替换为正确译文，返回其目录。"""
    (en_skill / "SKILL.md").write_text(ZH_SKILL, encoding="utf-8")
    return en_skill
