#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能汉化·第 4 步：把译文与备份逐项比对，检查翻译是否破坏技能。

仅使用 Python 标准库（3.8+）。

用法:
    python verify.py <技能目录> --backup <备份目录> [--json 报告.json]

判定:
    [ERROR] 必须修复（否则技能会坏）
    [WARN]  建议人工确认（可能是合理改动）
    [INFO]  仅提示（例如残留英文段落）

退出码: 0 无 ERROR；1 存在 ERROR。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillpaths import describe_roots, resolve_target as _platform_resolve  # noqa: E402

TEXT_EXT = {".md", ".markdown", ".mdx", ".txt", ".rst", ".text"}
CODE_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".zsh",
    ".ps1", ".bat", ".cmd", ".rb", ".go", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".rs", ".php", ".sql", ".lua", ".r", ".swift", ".kt", ".pl",
}
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)
FENCE_OPEN_RE = re.compile(r"^[ \t]*```", re.MULTILINE)
FENCE_BLOCK_RE = re.compile(r"^[ \t]*```([^\n`]*)\r?\n(.*?)^[ \t]*```[ \t]*$", re.DOTALL | re.MULTILINE)
# 这些语言的围栏里装的是散文/示意内容，允许翻译；其余（含无语言标记）视为代码，一字不改
TRANSLATABLE_FENCES = {"text", "txt", "plain", "plaintext", "markdown", "md", "log", "output", "console"}
INLINE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_URL_STOP = " \t\r\n" + '"' + "'<>)]}，。；、"
URL_RE = re.compile("https?://[^" + re.escape(_URL_STOP) + "]+")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
HEAD_RE = re.compile(r"^(#{1,6})[ \t]+\S", re.MULTILINE)
# 英文虚词表：用于区分「英文段落」与「命令行/标识符堆砌」，命中 <2 个即判定为代码行
PROSE_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "to", "of",
    "and", "or", "not", "for", "with", "without", "from", "into", "on", "in",
    "at", "by", "as", "if", "then", "than", "that", "this", "these", "those",
    "you", "your", "yours", "we", "our", "it", "its", "they", "their",
    "when", "where", "which", "who", "how", "why", "what",
    "can", "will", "would", "should", "must", "may", "might", "need", "use",
    "used", "using", "make", "makes", "get", "gets", "have", "has", "had",
    "do", "does", "did", "so", "but", "also", "only", "each", "every", "all",
    "some", "any", "more", "most", "other", "same", "such", "about", "after",
    "before", "while", "because", "however", "therefore", "instead",
}

ERRORS, WARNS, INFOS = [], [], []


def err(path, msg):
    ERRORS.append("%s :: %s" % (path, msg))


def warn(path, msg):
    WARNS.append("%s :: %s" % (path, msg))


def info(path, msg):
    INFOS.append("%s :: %s" % (path, msg))


def cjk_ratio(text):
    total = len(re.sub(r"\s", "", text))
    return round(len(CJK_RE.findall(text)) / total, 3) if total else 0.0


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return None
    keys, name, desc = [], None, None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_.\-]+)[ \t]*:[ \t]*(.*)$", line)
        if km:
            keys.append(km.group(1))
            if km.group(1) == "name":
                name = km.group(2).strip().strip("\"'")
            if km.group(1) == "description":
                desc = km.group(2).strip()
    return {"keys": keys, "name": name, "description": desc}


def diff_sets(name, old, new, path, limit=8, level="warn"):
    old_s, new_s = set(old), set(new)
    missing = sorted(old_s - new_s)
    added = sorted(new_s - old_s)
    if not missing and not added:
        return
    def brief(items):
        out = []
        for s in items[:limit]:
            s = re.sub(r"\s+", " ", str(s))[:90]
            out.append(s)
        more = "" if len(items) <= limit else " …等 %d 项" % len(items)
        return "; ".join(out) + more
    if missing:
        (err if level == "error" else warn)(path, "%s 丢失 %d 项 → %s" % (name, len(missing), brief(missing)))
    if added:
        (err if level == "error" else warn)(path, "%s 新增 %d 项 → %s" % (name, len(added), brief(added)))


def split_fences(text):
    """把围栏块拆成「代码块」与「可翻译文本块」两组。"""
    code, prose = [], []
    for info, body in FENCE_BLOCK_RE.findall(text):
        lang = info.strip().lower()
        (prose if lang in TRANSLATABLE_FENCES else code).append(body)
    return code, prose


def english_prose_lines(text):
    out, in_fence, in_fm = [], False, False
    lines = text.splitlines()
    # 跳过 frontmatter 区域（那里的 *_en 字段本就该是英文）
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1:]
                break
    for i, line in enumerate(lines, 1):
        if re.match(r"^[ \t]*```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = line.strip()
        if not s or CJK_RE.search(s):
            continue
        if re.match(r"^#{1,6}\s", s):
            continue
        if s.startswith("|") or re.match(r"^[-*_]{3,}$", s):
            continue
        if re.match(r"^\s*[-*+]\s*\[[ xX]\]", s):
            continue
        # 整行就是一个 URL / 路径 / 单个标识符的，跳过
        if re.match(r"^https?://\S+$", s) or re.match(r"^[-\w./\\]+$", s):
            continue
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", s)
        if len(words) < 6 or len(s) < 40:
            continue
        # 命令行 / 占位符行不是「英文段落」：靠英文虚词密度区分自然语言与代码
        if sum(1 for w in words if w.lower() in PROSE_STOPWORDS) < 2:
            continue
        out.append((i, s[:80]))
    return out


def check_text(rel, cur: Path, old: Path):
    t_new, t_old = read(cur), read(old)
    p = rel

    # 1) 结构：代码块配对
    fences = FENCE_OPEN_RE.findall(t_new)
    if len(fences) % 2 != 0:
        err(p, "代码块 ``` 未配对（共 %d 个，应为偶数）——译文很可能被截断" % len(fences))

    # 2) frontmatter
    fm_new, fm_old = frontmatter(t_new), frontmatter(t_old)
    if fm_old and not fm_new:
        err(p, "frontmatter 丢失或格式损坏（开头必须是 --- 包裹的 YAML）")
    elif fm_new and fm_old:
        if fm_old.get("name") != fm_new.get("name"):
            err(p, "frontmatter 的 name 被改动：%r → %r（必须保持原样）"
                % (fm_old.get("name"), fm_new.get("name")))
        lost = [k for k in fm_old["keys"] if k not in fm_new["keys"]]
        if lost:
            err(p, "frontmatter 丢失字段: %s" % ", ".join(lost))
        if not fm_new.get("description"):
            warn(p, "frontmatter 缺少 description")
        elif fm_new.get("description") == fm_old.get("description"):
            warn(p, "description 与原文完全相同，可能未翻译")

    # 3) 代码块内容必须一字不改；文本类围栏（```text 等）允许翻译，只核对数量
    code_old, prose_old = split_fences(t_old)
    code_new, prose_new = split_fences(t_new)
    diff_sets("代码块内容", code_old, code_new, p, limit=3, level="error")
    if len(code_old) != len(code_new):
        err(p, "代码块数量变化: %d → %d" % (len(code_old), len(code_new)))
    if len(prose_old) != len(prose_new):
        err(p, "文本类围栏（```text 等）数量变化: %d → %d" % (len(prose_old), len(prose_new)))

    # 4) 行内代码 / 链接 / URL
    diff_sets("行内代码", INLINE_RE.findall(t_old), INLINE_RE.findall(t_new), p, limit=10)
    diff_sets("链接目标", LINK_RE.findall(t_old), LINK_RE.findall(t_new), p, limit=10)
    diff_sets("URL", URL_RE.findall(t_old), URL_RE.findall(t_new), p, limit=10)

    # 5) 标题结构
    h_old = HEAD_RE.findall(t_old)
    h_new = HEAD_RE.findall(t_new)
    if h_old != h_new:
        if len(h_old) == len(h_new):
            warn(p, "标题层级与原文不一致（数量相同，层级被改）")
        else:
            warn(p, "标题数量变化: %d → %d" % (len(h_old), len(h_new)))

    # 6) 翻译覆盖率
    r_old, r_new = cjk_ratio(t_old), cjk_ratio(t_new)
    if r_old < 0.10 and r_new < 0.15:
        warn(p, "中文字符占比仅 %.2f（原文 %.2f）——疑似未翻译" % (r_new, r_old))
    elif r_new < r_old:
        warn(p, "中文字符占比下降 %.2f → %.2f" % (r_old, r_new))

    # 7) 残留英文段落
    left = english_prose_lines(t_new)
    if left:
        preview = " | ".join("L%d: %s" % (i, s) for i, s in left[:6])
        info(p, "疑似残留英文段落 %d 处 → %s" % (len(left), preview))


def check_code(rel, cur: Path, old: Path):
    try:
        if cur.read_bytes() != old.read_bytes():
            warn(rel, "代码文件内容被修改（规则要求默认保持原样；若只译了注释请人工确认）")
    except OSError as e:
        err(rel, "读取失败: %s" % e)


def main() -> int:
    ap = argparse.ArgumentParser(description="技能汉化校验")
    ap.add_argument("skill_dir", help="技能目录 / SKILL.md 路径 / 已安装的技能名")
    ap.add_argument("--backup", required=True, help="prepare.py 打印的备份目录")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    cur_root = _platform_resolve(args.skill_dir)
    old_root = Path(args.backup).expanduser().resolve()
    if cur_root is None or not cur_root.is_dir():
        print("[ERROR] 技能目录不存在: %s" % args.skill_dir)
        print(describe_roots())
        return 1
    if not old_root.is_dir():
        print("[ERROR] 备份目录不存在: %s" % old_root)
        return 1

    text_files = sorted(
        p for p in old_root.rglob("*")
        if p.is_file() and p.suffix.lower() in TEXT_EXT
    )
    if not text_files:
        print("[WARN] 备份里没有找到可翻译的文本文件，无事可做")

    for old in text_files:
        rel = old.relative_to(old_root).as_posix()
        cur = cur_root / rel
        if not cur.is_file():
            err(rel, "译文文件丢失（原文存在但译文不存在）")
            continue
        check_text(rel, cur, old)

    # 代码/数据文件是否被误改
    for old in sorted(old_root.rglob("*")):
        if not old.is_file():
            continue
        if old.suffix.lower() not in CODE_EXT:
            continue
        rel = old.relative_to(old_root).as_posix()
        cur = cur_root / rel
        if not cur.is_file():
            err(rel, "文件丢失")
        else:
            check_code(rel, cur, old)

    # 新增文件提示
    for cur in sorted(cur_root.rglob("*")):
        if cur.is_file() and not (old_root / cur.relative_to(cur_root)).exists():
            info(cur.relative_to(cur_root).as_posix(), "这是新增文件（原文没有）")

    if (cur_root / "SKILL.md").is_file():
        fm = frontmatter(read(cur_root / "SKILL.md"))
        if not fm or not fm.get("name"):
            err("SKILL.md", "缺少 frontmatter 或 name 字段")
        elif not fm.get("description"):
            err("SKILL.md", "缺少 frontmatter description 字段")

    print("=" * 72)
    print("校验对象: %s" % cur_root)
    print("对照备份: %s" % old_root)
    print("=" * 72)
    for tag, bucket in (("[ERROR]", ERRORS), ("[WARN]", WARNS), ("[INFO]", INFOS)):
        for line in bucket:
            print("%s %s" % (tag, line))
    print("-" * 72)
    print("ERROR %d / WARN %d / INFO %d" % (len(ERRORS), len(WARNS), len(INFOS)))
    if ERRORS:
        print("=> 存在 ERROR，必须修复后重跑校验。")
    elif WARNS:
        print("=> 无 ERROR，WARN 请逐条判断是否为合理改动。")
    else:
        print("=> 通过。")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"errors": ERRORS, "warnings": WARNS, "infos": INFOS},
                       ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
