#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能目录适配层：自动发现各家 AI 编程工具的技能根目录。

支持的平台（存在即纳入）:
    WorkBuddy   ~/.workbuddy-ai/skills        项目: .workbuddy-ai/skills
    Claude Code ~/.claude/skills              项目: .claude/skills
    Cursor      ~/.cursor/skills              项目: .cursor/skills
    Codex       ~/.codex/skills               项目: .codex/skills
    Agents      ~/.agents/skills              项目: .agents/skills

覆盖方式（优先级最高）:
    export SKILL_ZH_ROOTS="/path/a:/path/b"   # Windows 用分号分隔

仅使用 Python 标准库（3.8+）。
"""
from __future__ import annotations

import os
from pathlib import Path

ENV_SKILL_ROOTS = "SKILL_ZH_ROOTS"

# (用户级子路径, 项目级子路径, 显示名)
PLATFORMS = (
    (".workbuddy-ai/skills", ".workbuddy-ai/skills", "WorkBuddy"),
    (".claude/skills", ".claude/skills", "Claude Code"),
    (".cursor/skills", ".cursor/skills", "Cursor"),
    (".codex/skills", ".codex/skills", "Codex"),
    (".agents/skills", ".agents/skills", "Agents"),
)

# 插件/内置技能缓存目录（只扫一层，避免走进 node_modules 之类）
PLUGIN_CACHE_DIRS = (
    ".workbuddy-ai/plugins/cache",
    ".claude/plugins/cache",
)


def _env_roots():
    """读取 SKILL_ZH_ROOTS 环境变量，返回 [(label, Path)]；未设置则返回 None。"""
    raw = os.environ.get(ENV_SKILL_ROOTS, "").strip()
    if not raw:
        return None
    out = []
    for item in raw.split(os.pathsep):
        item = item.strip()
        if not item:
            continue
        p = Path(item).expanduser()
        if p.is_dir():
            out.append(("自定义(%s)" % p.name, p))
    return out or None


def _plugin_roots(home: Path):
    out = []
    for rel in PLUGIN_CACHE_DIRS:
        cache = home / rel
        if not cache.is_dir():
            continue
        for p in sorted(cache.glob("*/*/skills")):
            if p.is_dir():
                out.append(("插件缓存(%s)" % p.parent.parent.name, p))
    return out


def search_roots(include_plugins: bool = False, cwd: Path = None) -> list:
    """返回所有存在的技能根目录，元素为 (label, Path)。"""
    env = _env_roots()
    if env is not None:
        return env

    home = Path.home()
    cwd = Path(cwd) if cwd else Path.cwd()
    roots = []

    for user_rel, proj_rel, label in PLATFORMS:
        up = home / user_rel
        if up.is_dir():
            roots.append((label, up))
        pp = cwd / proj_rel
        if pp.is_dir() and pp.resolve() != up.resolve():
            roots.append((label + "(项目)", pp))

    if include_plugins:
        roots.extend(_plugin_roots(home))

    return roots


def resolve_target(arg: str, include_plugins: bool = True):
    """把「目录路径 / SKILL.md 路径 / 已安装的技能名」统一解析成技能目录。

    解析失败返回 None。
    """
    p = Path(arg).expanduser()
    if p.is_dir():
        return p.resolve()
    if p.is_file():
        return p.resolve().parent

    # 当作技能名搜索
    for _label, root in search_roots(include_plugins=include_plugins):
        cand = root / arg
        if cand.is_dir():
            return cand.resolve()
        for hit in root.glob("*/skills/" + arg):
            if hit.is_dir():
                return hit.resolve()
    return None


def describe_roots(include_plugins: bool = False) -> str:
    """人读的平台发现结果，用于报错时提示用户。"""
    roots = search_roots(include_plugins=include_plugins)
    if not roots:
        return ("未发现任何技能目录。可用环境变量 %s 指定，例如:\n"
                "  export %s=\"$HOME/.claude/skills\"" % (ENV_SKILL_ROOTS, ENV_SKILL_ROOTS))
    lines = ["已发现的技能目录:"]
    for label, path in roots:
        lines.append("  [%s] %s" % (label, path))
    return "\n".join(lines)
