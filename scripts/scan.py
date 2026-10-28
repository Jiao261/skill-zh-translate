#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能汉化·批量扫描：找出所有「还没汉化」的技能，按工作量从小到大排序。

仅使用 Python 标准库（3.8+）。

用法:
    python scan.py [--json 报告.json] [--threshold 0.15] [--roots 目录1,目录2]
                   [--include-plugins] [--limit N] [--todo-only]

判定标准:
    读技能根目录的 SKILL.md，算中文字符占比 cjk_ratio。
    cjk_ratio < threshold  → 待汉化 (todo)
    cjk_ratio >= threshold → 已汉化 (done)

退出码: 0 正常；2 存在待汉化技能（方便自动化里做判断）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillpaths import ensure_utf8_output, search_roots as _platform_roots  # noqa: E402

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TEXT_EXT = {".md", ".markdown", ".mdx", ".txt", ".rst", ".text"}
SKIP_DIRS = {
    ".git", ".svn", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".idea", ".vscode", ".pytest_cache", ".mypy_cache", "dist", "build", ".cache",
}
META_FILES = ("_skillhub_meta.json", "_knot_meta.json")


def cjk_ratio(text: str) -> float:
    total = len(re.sub(r"\s", "", text))
    return round(len(CJK_RE.findall(text)) / total, 3) if total else 0.0


def default_roots(include_plugins: bool) -> list:
    """跨平台发现技能根目录（WorkBuddy / Claude Code / Cursor / Codex / Agents）。"""
    return _platform_roots(include_plugins=include_plugins)


def find_skill_dirs(root: Path, max_depth: int = 6) -> list:
    """在 root 下找出所有含 SKILL.md 的目录（含 root 自身）。"""
    found, root = [], root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        if "SKILL.md" in filenames:
            found.append(Path(dirpath))
            dirnames[:] = []  # 技能内部不再往下找
    return found


def inspect(skill: Path) -> dict:
    md = skill / "SKILL.md"
    try:
        text = md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    ratio = cjk_ratio(text)

    total_bytes, n_files = 0, 0
    for dirpath, dirnames, filenames in os.walk(skill):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix.lower() in TEXT_EXT:
                try:
                    total_bytes += (Path(dirpath) / fn).stat().st_size
                except OSError:
                    pass
                n_files += 1

    meta = next((skill / m for m in META_FILES if (skill / m).is_file()), None)
    user_modified = None
    if meta:
        try:
            user_modified = bool(json.loads(meta.read_text(encoding="utf-8")).get("userModified"))
        except Exception:
            user_modified = None

    return {
        "name": skill.name,
        "path": str(skill),
        "cjk_ratio": ratio,
        "text_bytes": total_bytes,
        "text_files": n_files,
        "has_meta": meta is not None,
        "meta_file": meta.name if meta else None,
        "user_modified": user_modified,
    }


def main() -> int:
    ensure_utf8_output()
    ap = argparse.ArgumentParser(description="扫描所有未汉化的技能")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--threshold", type=float, default=0.15, help="中文占比低于该值视为待汉化")
    ap.add_argument("--roots", help="逗号分隔的自定义根目录")
    ap.add_argument("--include-plugins", action="store_true", help="连同插件缓存里的内置技能一起扫")
    ap.add_argument("--limit", type=int, default=0, help="只输出前 N 个（按工作量升序）")
    ap.add_argument("--todo-only", action="store_true", help="只列待汉化的")
    args = ap.parse_args()

    if args.roots:
        roots = [("自定义", Path(r.strip()).expanduser()) for r in args.roots.split(",") if r.strip()]
        roots = [(l, p) for l, p in roots if p.is_dir()]
    else:
        roots = default_roots(args.include_plugins)

    if not roots:
        from skillpaths import describe_roots
        print("[ERROR] 没找到任何技能根目录")
        print(describe_roots(include_plugins=args.include_plugins))
        return 1

    seen, rows = set(), []
    for label, root in roots:
        for skill in find_skill_dirs(root):
            key = str(skill).lower()
            if key in seen:
                continue
            seen.add(key)
            rec = inspect(skill)
            rec["source"] = label
            rec["status"] = "done" if rec["cjk_ratio"] >= args.threshold else "todo"
            rows.append(rec)

    todo = [r for r in rows if r["status"] == "todo"]
    done = [r for r in rows if r["status"] == "done"]
    todo.sort(key=lambda r: (r["text_bytes"], r["name"]))
    done.sort(key=lambda r: r["name"])

    print("=" * 78)
    print("技能汉化·总览   共 %d 个技能：待汉化 %d / 已汉化 %d" % (len(rows), len(todo), len(done)))
    print("判定阈值：SKILL.md 中文字符占比 < %.2f 即视为待汉化" % args.threshold)
    print("=" * 78)

    # 默认视图：待汉化（按文本量升序）在前，已汉化在后，保证「从上往下做」始终成立
    show = todo if args.todo_only else todo + done
    if args.limit:
        show = show[: args.limit]

    if show:
        print("\n%-30s %8s %7s %6s %s" % ("技能名", "文本量", "中文占比", "文件数", "来源"))
        print("-" * 78)
        for r in show:
            flag = ""
            if r["user_modified"]:
                flag = " [已标记userModified]"
            print("%-30s %8s %7.2f %6d %s%s" % (
                r["name"][:30],
                ("%.0fKB" % (r["text_bytes"] / 1024)) if r["text_bytes"] >= 1024 else ("%dB" % r["text_bytes"]),
                r["cjk_ratio"], r["text_files"], r["source"], flag,
            ))
        if args.limit and len(todo) > args.limit:
            print("… 还有 %d 个待汉化未显示（--limit %d）" % (len(todo) - args.limit, args.limit))

    if todo:
        total_kb = sum(r["text_bytes"] for r in todo) / 1024
        print("\n待汉化合计文本量约 %.0f KB。建议从小往大做（上面的顺序即是）。" % total_kb)
    else:
        print("\n全部已汉化，无需处理。")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"threshold": args.threshold, "todo": todo, "done": done},
                       ensure_ascii=False, indent=2), encoding="utf-8")

    return 2 if todo else 0


if __name__ == "__main__":
    sys.exit(main())
