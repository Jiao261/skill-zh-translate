#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能汉化·第 1 步：定位技能 -> 清点文件 -> 分类 -> 自动备份。

仅使用 Python 标准库（3.8+）。

用法:
    python prepare.py <技能目录|SKILL.md路径|zip包|技能名> [--json 报告.json]
                      [--no-backup] [--backup-dir 目录]

退出码: 0 正常；1 出错（找不到目标 / 备份失败）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillpaths import describe_roots, resolve_target as _platform_resolve  # noqa: E402

TEXT_EXT = {".md", ".markdown", ".mdx", ".txt", ".rst", ".text"}
CODE_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".zsh",
    ".ps1", ".bat", ".cmd", ".rb", ".go", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".rs", ".php", ".sql", ".lua", ".r", ".swift", ".kt", ".pl", ".vue", ".svelte",
}
DATA_EXT = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".csv",
    ".tsv", ".xml", ".html", ".htm", ".css", ".scss", ".less", ".svg", ".lock",
}
BIN_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".pdf", ".zip",
    ".tar", ".gz", ".tgz", ".7z", ".rar", ".woff", ".woff2", ".ttf", ".otf",
    ".eot", ".mp3", ".mp4", ".wav", ".mov", ".webm", ".xlsx", ".xls", ".docx",
    ".doc", ".pptx", ".ppt", ".db", ".sqlite", ".pyc", ".so", ".dll", ".exe", ".bin",
}
SKIP_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".idea", ".vscode", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".next",
    "dist", "build", ".cache",
}
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)


def die(msg: str) -> "None":
    print("[ERROR] " + msg, file=sys.stderr)
    sys.exit(1)


def extract_zip(zip_path: Path) -> Path:
    """把 zip 解压到同级目录，返回解压后的技能目录。"""
    dest = zip_path.parent / (zip_path.stem + "_extracted")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    # 压缩包常见一层外壳目录，剥掉不含 SKILL.md 的中间层
    cur = dest
    for _ in range(3):
        entries = [p for p in cur.iterdir() if p.name not in ("__MACOSX", ".DS_Store")]
        if len(entries) == 1 and entries[0].is_dir():
            cur = entries[0]
        else:
            break
    print("已解压到: %s" % cur)
    return cur


def resolve_target(arg: str) -> Path:
    p = Path(arg).expanduser()
    if p.is_file() and p.suffix.lower() == ".zip":
        return extract_zip(p)
    hit = _platform_resolve(arg)
    if hit is None:
        die("找不到目标技能: %s（请给出目录路径、SKILL.md 路径、zip 包或已安装的技能名）\n%s"
            % (arg, describe_roots()))
    return hit


def sniff_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TEXT_EXT:
        return "translate"
    if ext in CODE_EXT:
        return "code"
    if ext in DATA_EXT:
        return "data"
    if ext in BIN_EXT:
        return "binary"
    try:
        head = path.open("rb").read(4096)
    except OSError:
        return "binary"
    if b"\x00" in head:
        return "binary"
    return "data"


def cjk_ratio(text: str) -> float:
    total = len(re.sub(r"\s", "", text))
    if not total:
        return 0.0
    return round(len(CJK_RE.findall(text)) / total, 3)


def parse_frontmatter(text: str):
    m = FM_RE.match(text)
    if not m:
        return None
    keys, name = [], None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_.\-]+)[ \t]*:[ \t]*(.*)$", line)
        if km:
            k = km.group(1)
            keys.append(k)
            if k == "name":
                name = km.group(2).strip().strip("\"'")
    return {"keys": keys, "name": name}


def walk_files(skill: Path) -> list:
    out = []
    for dirpath, dirnames, filenames in os.walk(skill):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git"))
        for fn in sorted(filenames):
            out.append(Path(dirpath) / fn)
    return out


def backup(skill: Path, backup_dir) -> Path:
    # 备份位置与具体平台无关，避免绑死在某一家工具的目录里
    root = Path(backup_dir).expanduser() if backup_dir else (
        Path.home() / ".skill-zh-backups"
    )
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = root / ("%s-%s" % (skill.name, ts)) / skill.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        skill, dest, ignore=shutil.ignore_patterns(*SKIP_DIRS), dirs_exist_ok=False
    )
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="技能汉化前置脚本：清点 + 备份")
    ap.add_argument("target", help="技能目录 / SKILL.md 路径 / zip 包 / 技能名")
    ap.add_argument("--json", dest="json_out", help="把机器可读报告写到该路径")
    ap.add_argument("--no-backup", action="store_true", help="不备份（不推荐）")
    ap.add_argument("--backup-dir", help="备份根目录，默认 ~/.skill-zh-backups")
    args = ap.parse_args()

    skill = resolve_target(args.target)
    if not (skill / "SKILL.md").is_file():
        print("[WARN] 该目录下没有 SKILL.md，可能不是技能包（仍继续清点）", file=sys.stderr)

    records, order = [], {"translate": [], "code": [], "data": [], "binary": []}
    for f in walk_files(skill):
        rel = f.relative_to(skill).as_posix()
        kind = sniff_kind(f)
        try:
            size = f.stat().st_size
        except OSError:
            size = 0
        rec = {"path": rel, "kind": kind, "bytes": size}
        if kind == "translate":
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            fm = parse_frontmatter(text)
            rec.update(
                lines=len(text.splitlines()),
                cjk_ratio=cjk_ratio(text),
                has_frontmatter=fm is not None,
                frontmatter_keys=(fm or {}).get("keys", []),
                frontmatter_name=(fm or {}).get("name"),
                already_zh=cjk_ratio(text) >= 0.25,
            )
        records.append(rec)
        order[kind].append(rel)

    # SKILL.md 优先
    order["translate"].sort(key=lambda r: (r != "SKILL.md", r.count("/"), r))

    bak = None
    if not args.no_backup:
        try:
            bak = backup(skill, args.backup_dir)
        except OSError as e:
            die("备份失败，已中止（未修改任何文件）: %s" % e)

    report = {
        "skill_dir": str(skill),
        "skill_name": skill.name,
        "backup_dir": str(bak) if bak else None,
        "files": records,
        "order": order,
    }
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print("=" * 72)
    print("技能目录 : %s" % skill)
    print("技能名称 : %s（目录名与文件名一律不要改）" % skill.name)
    print("备份路径 : %s" % (bak if bak else "（已跳过备份）"))
    print("=" * 72)
    label = {"translate": "待翻译 (translate)", "code": "代码·默认不动 (code)",
             "data": "数据·默认不动 (data)", "binary": "二进制·跳过 (binary)"}
    for kind in ("translate", "code", "data", "binary"):
        if not order[kind]:
            continue
        print("\n## %s — %d 个" % (label[kind], len(order[kind])))
        for rec in [r for r in records if r["kind"] == kind]:
            if kind == "translate":
                print("  %-58s %5d行  中文占比%.2f%s%s" % (
                    rec["path"], rec.get("lines", 0), rec.get("cjk_ratio", 0.0),
                    "  [含frontmatter]" if rec.get("has_frontmatter") else "",
                    "  [疑似已是中文→可跳过]" if rec.get("already_zh") else "",
                ))
            else:
                print("  %-58s %6d B" % (rec["path"], rec["bytes"]))

    print("\n翻译顺序建议：")
    for i, rel in enumerate(order["translate"], 1):
        print("  %d. %s" % (i, rel))
    if not order["translate"]:
        print("  （没有找到可翻译的文本文件）")
    print("\n下一步：读取 references/translation-rules.md，再逐文件翻译。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
