# 技能汉化·翻译规则手册

翻译前必读。本文件是「怎么译」的唯一依据，不要凭感觉发挥。

---

## 一、总原则

1. **目标读者是 AI 智能体，不是人类读者。** 译文的用途是让模型照做，所以要求：指令明确、术语一致、不啰嗦、不文学化。宁可直白，不要华丽。
2. **只做翻译，不做优化。** 不新增章节、不删减内容、不合并列表、不"顺手改进"原文写得不好的地方、不加译者注（除非术语必须保留英文）。
3. **译意不译字。** 英文长句按中文技术文档习惯重组（英文用从句，中文拆成短句；英文被动改中文主动）。但**信息量必须一比一**，不能漏掉任何一个条件、限制、例外、注意事项。
4. **不确定就保留英文。** 拿不准的术语写成「中文（English）」，绝不臆造译名。

---

## 二、绝对不译清单（原样照抄）

以下内容一旦改动，技能可能直接失效：

| 类别 | 示例 | 说明 |
|---|---|---|
| 技能目录名 / 文件名 | `pdf-tools/`, `scripts/rotate.py` | 改名会断掉所有路径引用 |
| frontmatter 的 `name` 值 | `name: pdf-tools` | 技能标识符，保持英文小写连字符 |
| 其他 frontmatter 键名 | `description:`, `allowed-tools:` | 只译值，不译键名 |
| 围栏**代码**块内部 | ` ```bash ... ``` `、` ```json ... ``` ` | 一字不改，含注释 |
| 散文类围栏内部 | ` ```text ... ``` `、` ```plain ... ``` ` | **可以翻译**（装的是示意/散文，不是代码） |
| 行内代码 | `` `--flag` ``、`` `SKILL.md` `` | 命令、参数、路径、变量名、函数名、类名、包名 |
| URL / 邮箱 | `https://...` | 包括 Markdown 链接的 `(...)` 目标 |
| Markdown 链接目标 | `[文档](references/x.md)` | 只译方括号里的显示文字 |
| 占位符 | `{variable}`、`$VAR`、`%s`、`<skill_dir>`、`{{name}}` | 保留原样 |
| 文件路径 | `~/.workbuddy-ai/skills/`、`./assets/logo.png` | 含 Windows 反斜杠路径 |
| 命令与参数 | `npm install`、`--dry-run`、`-v` | 包括选项说明中的短横线形式 |
| 环境变量 | `$HOME`、`%APPDATA%`、`API_KEY` | |
| 代码标识符 | `camelCase`、`snake_case`、`ClassName` | 出现在正文里也不译 |
| API / 协议 / 标准名 | `REST`、`JSON`、`OAuth 2.0`、`HTTP 404` | 通用缩写保留 |
| 厂商与产品名 | `GitHub`、`Figma`、`Anthropic` | 有官方中文名的用中文（如「微软」） |
| 包名与依赖 | `requests`、`playwright`、`@scope/pkg` | 不译、不加引号 |
| 日期时间格式串 | `YYYY-MM-DD`、`HH:mm:ss` | |
| HTML / XML 标签 | `<div>`、`<svg viewBox="...">` | |
| YAML/JSON 片段 | 配置示例 | 键与值都保留 |
| 表情、徽章、分隔线 | `🚀`、`![badge](...)`、`---` | 视觉元素保留 |
| 版权与许可原文 | `MIT License` | 保留，必要时加中文注释说明 |

---

## 三、术语对照表（统一口径）

| English | 中文 | 备注 |
|---|---|---|
| skill | 技能 | 指本类技能包 |
| SKILL.md | SKILL.md | 文件名不译 |
| frontmatter | 前置元数据（frontmatter） | 首次出现带英文 |
| description | 描述 | |
| workflow | 工作流 | |
| step | 步骤 | |
| trigger / trigger words | 触发词 | |
| agent | 智能体 | |
| prompt | 提示词 | |
| tool / tool call | 工具 / 工具调用 | |
| reference(s) | 参考文档 | 指 `references/` 目录 |
| script | 脚本 | |
| asset(s) | 资源文件 | 指 `assets/` 目录 |
| template | 模板 | |
| bundled resources | 内置资源 | |
| progressive disclosure | 渐进式披露 | 保持原义 |
| context / context window | 上下文 / 上下文窗口 | |
| token | token（词元） | 首次带英文 |
| output | 输出 / 产出 | 名词用「产出」，动词用「输出」 |
| input | 输入 | |
| placeholder | 占位符 | |
| dependency | 依赖 | |
| fallback | 兜底 / 降级方案 | |
| validate / validation | 校验 | |
| lint | 静态检查 | |
| best practice | 最佳实践 | |
| edge case | 边界情况 | |
| requirement | 需求 / 要求 | |
| instruction | 指令 | |
| example | 示例 | |
| note / warning | 注意 / 警告 | |
| usage | 用法 | |
| default | 默认 | |
| optional / required | 可选 / 必填 | |
| directory | 目录 | |
| file path | 文件路径 | |
| command line | 命令行 | |
| troubleshooting | 故障排查 | |

遇到表里没有的词：优先用业界通行译法；实在不确定就写「中文（English）」。

---

## 四、格式保留规则

翻译是"替换文字"，不是"重排版面"。必须逐项对齐：

1. **标题**：数量、层级（`#` 个数）、顺序完全一致。只译标题文字。
2. **列表**：条目数量一致，不合并、不拆分、不调整顺序；符号（`-` / `*` / `1.`）保持原样；缩进层级不变（嵌套列表尤其注意）。
3. **表格**：列数、行数、对齐行（`|---|---|`）不变，只译单元格文字。表头也要译。
4. **引用块**：`>` 前缀保留。
5. **代码块**：语言标记（```bash、```python、```json）保留；块内一字不改。语言标记是 `text` / `plain` / `markdown` 等**散文类**围栏时，内容可以翻译（术语可写成「中文（English）」）。
6. **行内代码**：反引号位置保留。
7. **空行**：段落之间的空行保留（影响 Markdown 渲染）。
8. **链接**：`[显示文字](目标)` 只译显示文字；图片 `![alt](src)` 的 alt 可译，src 不动。
9. **加粗 / 斜体**：`**...**`、`*...*` 的标记位置保留，只译内部文字。
10. **编号引用**：如「见第 3 步」「见 `references/x.md`」保持指向关系。

---

## 五、frontmatter 的处理

```yaml
---
name: pdf-tools          # ← 绝对不动
description: Rotate, merge, split PDFs. Use when the user says "rotate PDF".   # ← 译成中文，但保留英文触发词
agent_created: true      # ← 不动
allowed-tools: [Bash, Read]   # ← 不动
---
```

`description` 是技能被调用的唯一依据，译法要求：

- **译成中文**，但把原文里的**关键英文触发词原样保留在括号里**，例如：
  `description: 旋转、合并、拆分 PDF 文件。当用户说「旋转 PDF」「合并 PDF」（rotate PDF / merge PDF）时使用。`
- 保持第三人称、说明「这个技能做什么」+「什么时候用」两段式。
- 长度与原文相当，不要扩写成一段长文。
- **不要**把 description 写成纯英文不译，也不要译得看不出触发场景。

其他键（`name`、`allowed-tools`、`agent_created` 等）一律原样保留。

---

## 六、语体要求

- 用**祈使句**下指令：「运行脚本」而不是「你应该运行脚本」。
- 用**主动语态**：「脚本会生成报告」而不是「报告将被脚本生成」。
- 用**短句**，一个句子只说一件事。
- 术语全篇统一（同一概念从头到尾同一个译名，不要一会儿「智能体」一会儿「代理」）。
- 不要用「亲爱的用户」「请注意哦」这类客套语；保持专业克制。
- 原文的 `IMPORTANT` / `MUST` / `NEVER` 等强调词要译出同等强度：「必须」「禁止」「绝不能」，不要弱化成「建议」。
- 数字、单位、版本号（`v2.1.0`）、百分比保留原样。

---

## 七、特殊内容处理

- **HTML 注释**（`<!-- ... -->`）：翻译其中的说明文字。
- **TODO / FIXME**：翻译描述部分，保留 `TODO:` / `FIXME:` 标记本身。
- **`scripts/` 下的代码**：默认**完全不改**（含注释）。仅当用户明确要求「连注释也翻译」时，才翻译注释与文档字符串，且：
  - 绝不改标识符、字符串常量、正则、格式串；
  - 中文注释前加 `# `，保持原有缩进；
  - 改完必须能通过 `python -m py_compile` 之类的语法检查。
- **`assets/` 下的模板文件**：若是 `.md`/`.txt` 模板，可以翻译其中的说明文字；若是给程序读取的模板（含占位符），只译注释与说明，占位符保留。
- **`.json` / `.yaml` 配置文件**：默认不改。用户明确要求时只译值（value），键名（key）保留。
- **README / CHANGELOG**：正常翻译；CHANGELOG 里的版本号、日期、commit hash 保留。

---

## 八、交付前自检清单

翻译完每个文件，逐条过一遍：

- [ ] frontmatter 的 `name` 与原文完全一致
- [ ] 代码块成对出现，块内内容与原文一致
- [ ] 所有命令、参数、路径、URL 与原文一致
- [ ] 标题数量与层级与原文一致
- [ ] 列表条目数、表格行列数与原文一致
- [ ] 没有任何段落被漏译（英文段落残留）
- [ ] 术语全篇统一
- [ ] 没有新增原文不存在的内容

最后统一跑 `scripts/verify.py`，把 ERROR 清零。
