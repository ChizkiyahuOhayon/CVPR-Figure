<h1 align="center">CVPR-Figure</h1>

<p align="center">
  <a href="README.md"><b>English</b></a>
  &nbsp;|&nbsp;
  <b>简体中文</b>
</p>

<p align="center">
  <b>面向 AI 顶会论文的 pipeline / 框架图 / teaser 图生成 skill。</b><br>
  写一份简短的 spec，得到一张 <b>Visio 和 PowerPoint 原生可编辑</b> 的图，
  外加给 LaTeX 用的 PDF 和 600 dpi 高清 PNG。
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#安装">安装</a> ·
  <a href="#模板库">模板库</a> ·
  <a href="#编辑输出visiopowerpointillustrator">Visio</a> ·
  <a href="#审计器">审计器</a> ·
  <a href="#常见问题">常见问题</a>
</p>

<p align="center">
  <a href="https://github.com/ChizkiyahuOhayon/CVPR-Figure/actions/workflows/test.yml"><img alt="tests" src="https://github.com/ChizkiyahuOhayon/CVPR-Figure/actions/workflows/test.yml/badge.svg"></a>
  <img alt="MIT licence" src="https://img.shields.io/badge/licence-MIT-blue.svg">
  <img alt="Python 3.8+" src="https://img.shields.io/badge/python-3.8%2B-blue.svg">
  <img alt="no dependencies" src="https://img.shields.io/badge/dependencies-none-brightgreen.svg">
  <img alt="Claude Code and Codex" src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-8A2BE2.svg">
</p>

<p align="center">
  <img src="assets/gallery/pipeline-4stage.png" width="100%" alt="四阶段 pipeline 框架图">
</p>

---

## 为什么要做这个

AI 生成的框架图不是"丑"，而是**通用**。审稿人一秒就能认出来：

| AI 味的特征 | 真实顶会图的做法 |
|---|---|
| 高饱和彩虹配色，一个框一个颜色 | 3–5 种淡色调，每种只承载一个语义 |
| 投影、渐变、毛玻璃 | 纯平填充，一条黑色发丝描边 |
| 齿轮、大脑、云朵、闪光、emoji | 张量画成立体卡片，编码器画成梯形 |
| 方框里塞整句话 | 名词短语，不超过 6 个词 |
| 每个框一样大，排成完美网格 | 宽度承载重要性 |
| 飘着的曲线箭头，端点没对准 | 沿端口法向的正交走线 |
| 全篇没有一张真实数据 | 输入截图和输出渲染，直接嵌进去 |
| "图 1：所提出框架的总览。" | caption 陈述一个论断 |

上面每一条都是**默认行为**。`CVPR-Figure` 的做法不是"提示模型别这么画"，而是**把这些默认从引擎里拆掉**：

- 配色、字号、线宽、圆角、内边距，全部是用 PyMuPDF **从已发表 CVPR/ICCV/AAAI 论文 PDF 的矢量内容里量出来的**，不是自己编的（方法与数值见 [`references/house-style.md`](references/house-style.md)）；
- 版面由确定性求解器计算，**单位是最终印刷磅值**——spec 里写 `size: 7.0`，纸上就是 7.0 pt，不需要心算；
- 箭头被**强制**沿端口法向进出、直角转折；
- 交付前必须过**审计器**，它会把上面那些特征逐条点名。

### 一个决定了配色的发现

把 SparseWorld、GaussianWorld、EmbodiedOcc、StreamVGGT、TPVFormer 的图用 PyMuPDF 拆开看：填充色**恰好是 Microsoft Office 主题色的 tint 阶梯**，字体表里还残留着 `SimSun`、`SimHei`、`Calibri`——这些图是用**中文版 PowerPoint** 画的。

```
#92CDDC #B7DDE8 #DBEEF3   Office Accent5 的 40 / 60 / 80% 变浅
#FFD965 #FFE699 #FFF2CC   gold，同一阶梯
#ED7D31 #F8CBAD #FBE5D6   orange，同一阶梯
描边：#000000 出现 1191 次，第二名的颜色只有 20 次
```

所以本项目直接采用作者真正点过的那套色卡，而不是"更好看"的自创配色——后者一眼就不像；同时把 `.pptx` 导出做成一等公民，而不是附赠功能。

---

## 快速开始

零依赖、免安装。clone 下来直接出图：

```bash
git clone https://github.com/ChizkiyahuOhayon/CVPR-Figure.git
cd CVPR-Figure

python3 scripts/render.py examples/quickstart.yaml -o build/quickstart \
        -f svg,pdf,png,pptx,vsdx --dpi 600
```

```
wrote build/quickstart.svg
wrote build/quickstart.pdf
wrote build/quickstart.png
wrote build/quickstart.pptx
wrote build/quickstart.vsdx
  pdf via libreoffice
  png via pdftoppm @600 dpi -- 4147 x 1530 px
  pptx: 44 shapes, 0 embedded image(s)
  canvas 496.8 x 182.8 pt | 10 nodes | 8 edges | scale 1.000
```

<p align="center">
  <img src="assets/gallery/quickstart.png" width="92%" alt="快速开始示例图">
</p>

这张图来自 [`examples/quickstart.yaml`](examples/quickstart.yaml)，约 50 行。
用 PowerPoint 打开 `build/quickstart.pptx`、或用 Visio 打开 `build/quickstart.vsdx`，
拖一下方框试试：**每个元素都是原生形状，不需要"取消组合"**。

然后检查它：

```bash
python3 scripts/validate.py examples/quickstart.yaml --svg build/quickstart.svg
# 0 error(s), 0 warning(s), 0 note(s) | 497 x 183 pt | 10 nodes
```

---

## 安装

### 作为 Claude Code skill（推荐）

```bash
git clone https://github.com/ChizkiyahuOhayon/CVPR-Figure.git
cd CVPR-Figure
./install.sh              # -> ~/.claude/skills/cvpr-figure   （全局，所有项目可用）
./install.sh --project    # -> ./.claude/skills/cvpr-figure   （只在当前项目）
```

安装脚本会复制 skill、跑一遍自检、并报告找到了哪些可选转换器。

> 项目名是 **CVPR-Figure**，但装好的 skill id 是小写的 `cvpr-figure`——
> Claude Code 的 skill id 规定是小写连字符，所以斜杠后面要敲小写。

之后直接用自然语言提要求：

> 读一下 `method.tex`，给 CVPR 投稿画一张通栏的 overview 图。
> 导出 LaTeX 用的 PDF，再给我一份可编辑的 `.vsdx`。

Claude Code 会加载 [`SKILL.md`](SKILL.md)，填图表契约、选原型、写 spec、渲染、审计，最后把 LaTeX 代码块给你。也可以用 `/cvpr-figure` 显式调用。

### 配合 Codex / Cursor / Aider / 自建 API 循环

把 agent 指向 [`AGENTS.md`](AGENTS.md)——同样的指令，去掉了 Claude Code 的路由元数据：

```bash
git clone https://github.com/ChizkiyahuOhayon/CVPR-Figure.git third_party/CVPR-Figure
# 然后在你的 AGENTS.md / .cursorrules / system prompt 里写：
#   "任何框架图、pipeline 图、teaser 图、模块图，
#    都遵循 third_party/CVPR-Figure/AGENTS.md。"
```

`agents/openai.yaml` 里有给相应宿主读取的显示名和默认 prompt。

### 不用 agent，手动使用

引擎就是一个普通命令行工具。复制最接近的模板、改 YAML、渲染。
语法全在 [`references/spec-language.md`](references/spec-language.md)。

### 环境要求

| | |
|---|---|
| **必需** | Python 3.8+。仅此而已——引擎只用标准库 |
| **可选** | PyYAML（没装时用内置解析器，输出逐字节一致） |
| **出 `.pdf`** | Inkscape / LibreOffice / `rsvg-convert` / CairoSVG 任一 |
| **出 `.png` / `.tiff`** | `pdftoppm`（poppler-utils）或 ImageMagick |
| **出 `.emf`** | Inkscape 或 LibreOffice |

`.svg`、`.vsdx`、`.pptx` 由内置代码直接写出，**永远可用**。

<details>
<summary>安装可选转换器</summary>

```bash
# macOS
brew install --cask inkscape libreoffice
brew install poppler imagemagick

# Debian / Ubuntu
sudo apt install inkscape libreoffice-draw poppler-utils imagemagick librsvg2-bin

# 最小配置：poppler + librsvg 就够出 PDF 和高清 PNG
```
</details>

---

## 工作流程

三步。skill 会带着 agent 走完这三步；手动使用也是同样三步。

### 1. 图表契约——动笔前先答题

[`static/core/contract.md`](static/core/contract.md) 里有七个问题，第一个最关键：

> 这张图要让读者相信：______________________

如果这句话需要一个"并且"，说明它是两张图。如果写的是*"这是我们方法的架构"*——那是描述不是论断，画出来必然没有重点。

同时还要定：原型、哪一个元素是核心贡献、语义配色表、会场与栏宽、哪些真实截图会填进 image 槽位。

### 2. 写 spec——只写语义，不写像素

你说明**什么东西按什么顺序放在哪里**，几何由引擎算。

```yaml
figure: {id: overview, venue: cvpr, width: double, font: times}

layout: row
gap: 14

panels:
  - id: s_core
    title: "Our Contribution"          # 粗斜体，位于虚线容器上方
    frame: dashed
    fill: gold.pale
    body:
      - {id: q, shape: slab, n: 5, cell: 8, cellh: 26, role: attention}
      - group:                          # 带重复次数角标的着色子区域
          id: blk
          frame: region
          frame_color: gold.deep
          badge: "×L"
          body:
            - {id: b1, text: "Cross-Attention", role: core, outline: match}
            - {id: b2, text: "Feed Forward",    role: core, outline: match}

edges:
  - {from: q, to: blk, color: gold.deep}
  - {from: q.w, to: sum.w, route: bus, bend: 10, dash: true, label: "residual"}
```

有两个特性承担了绝大部分"看起来像手工排版"的效果：

- **等尺寸吸附**——列里的方框类兄弟节点吸附到最宽者，行里吸附到最高者，于是一摞模块自然落在网格上；
- **端口法向路由**——不管你指定什么走线方式，线一定沿源端口法向离开、沿目标端口法向进入，只走直角。箭头永远不会平贴着边缘扎进去。

### 3. 审计——交付之前

```bash
python3 scripts/validate.py spec.yaml --svg build/fig.svg
```

`FAIL` 必须清零，`WARN` 要么修要么给出理由。然后做
[`references/anti-ai-checklist.md`](references/anti-ai-checklist.md) 里的人眼复核：
眯眼测试、用手指顺一条通路、盖住 caption、转灰度。

---

## 模板库

复制最接近的那个，然后替换内容。从空白 spec 开始既费劲，又会丢掉让这个原型成立的比例关系。

一篇论文通常需要**一张 teaser 类 + 一到两张其他**。需要第三张框架图，几乎总是说明方法本身没拆干净。

### 架构类论文——贡献是一个模型

<table>
<tr>
<td width="50%"><a href="templates/pipeline-4stage.yaml"><img src="assets/gallery/pipeline-4stage.png" alt="pipeline-4stage"></a></td>
<td width="50%"><a href="templates/teaser-comparison.yaml"><img src="assets/gallery/teaser-comparison.png" alt="teaser-comparison"></a></td>
</tr>
<tr>
<td><b><code>pipeline-4stage</code></b><br><i>"整个流程有哪些部件？"</i><br>3–5 个虚线阶段容器，贡献所在阶段加淡色底，每阶段箭头一个颜色。双栏。</td>
<td><b><code>teaser-comparison</code></b><br><i>"这不就是 X 吗？"</i><br>范式行 (a)(b)(c…Ours) 共用同一套配色，让读者只看到算子变了。第 1 页，单栏。</td>
</tr>
<tr>
<td><a href="templates/module-detail.yaml"><img src="assets/gallery/module-detail.png" alt="module-detail"></a></td>
<td><a href="templates/attention-tokens.yaml"><img src="assets/gallery/attention-tokens.png" alt="attention-tokens"></a></td>
</tr>
<tr>
<td><b><code>module-detail</code></b><br><i>"公式和接线对得上吗？"</i><br>单个模块展开，算子显式画出，张量维度标注在边上。单栏。</td>
<td><b><code>attention-tokens</code></b><br><i>"这个注意力模式凭什么更好？"</i><br>token 按来源着色，穿过淡色注意力区域。双栏。</td>
</tr>
<tr>
<td><a href="templates/streaming-worldmodel.yaml"><img src="assets/gallery/streaming-worldmodel.png" alt="streaming-worldmodel"></a></td>
<td><a href="templates/dual-branch.yaml"><img src="assets/gallery/dual-branch.png" alt="dual-branch"></a></td>
</tr>
<tr>
<td><b><code>streaming-worldmodel</code></b><br><i>"帧与帧之间记住了什么？"</i><br>嵌套容器 + 时间轨；标签文字与所属数据流同色。双栏。</td>
<td><b><code>dual-branch</code></b><br><i>"两个分支是什么关系？"</i><br>师生 / 对比 / EMA。分支严格平行，stop-grad 用虚线。双栏。</td>
</tr>
<tr>
<td colspan="2"><a href="templates/gated-module.yaml"><img src="assets/gallery/gated-module.png" width="49%" alt="gated-module"></a>
<br><b><code>gated-module</code></b> —— <i>"你到底改了什么、冻了什么？"</i><br>
adapter、LoRA、FiLM、校准头。一条泳道冻结直通，其余被门控调制。两个算子**水平错开**，让每个门控从正下方垂直进入它驱动的那个算子，<b>零交叉</b>。单栏。</td>
</tr>
</table>

### 分析 / 评测 / 立场类论文——没有网络可画

这几个存在的理由是：测量类论文同样有一条论证线，而图要承载的正是这条论证线。

<table>
<tr>
<td width="50%"><a href="templates/blindspot-teaser.yaml"><img src="assets/gallery/blindspot-teaser.png" alt="blindspot-teaser"></a></td>
<td width="50%"><a href="templates/factorial-2x2.yaml"><img src="assets/gallery/factorial-2x2.png" alt="factorial-2x2"></a></td>
</tr>
<tr>
<td><b><code>blindspot-teaser</code></b><br><i>"现有指标看不见什么？"</i><br>把子集关系画成<b>嵌套区域</b>，于是每个评估器只需要一根箭头，零交叉。第 1 页，单栏。</td>
<td><b><code>factorial-2x2</code></b><br><i>"受控设计隔离出了什么？"</i><br>两个因子交叉成四个条件，只有一格承载论断。单栏。</td>
</tr>
<tr>
<td><a href="templates/study-overview.yaml"><img src="assets/gallery/study-overview.png" alt="study-overview"></a></td>
<td><a href="templates/taxonomy.yaml"><img src="assets/gallery/taxonomy.png" alt="taxonomy"></a></td>
</tr>
<tr>
<td><b><code>study-overview</code></b><br><i>"这项研究整体是什么形状？"</i><br>数据与工况 → 受控设计 → 诊断 → 补救<i>及其边界</i>。双栏。</td>
<td><b><code>taxonomy</code></b><br><i>"这项工作坐在领域的哪一格？"</i><br>领域划分，只有被占据的格子上色。引言 / 相关工作，双栏。</td>
</tr>
</table>

每个原型的完整规则和典型翻车方式，见 [`references/archetypes.md`](references/archetypes.md)。

---

## 输出格式

```bash
python3 scripts/render.py spec.yaml -o build/fig \
        -f svg,pdf,png,tiff,emf,vsdx,pptx --dpi 600
```

| 格式 | 由谁写出 | 可在哪里编辑 |
|---|---|---|
| `.svg` | 内置 | Illustrator、Inkscape、Figma、Affinity、浏览器 |
| `.vsdx` | **内置** | **Visio 原生编辑，不需要取消组合** |
| `.pptx` | **内置** | **PowerPoint 原生编辑；复制粘贴进 Visio 仍是形状** |
| `.pdf` | 自动挑已安装的转换器 | LaTeX `\includegraphics`、Illustrator |
| `.png` / `.tiff` | 按 `--dpi` 从 PDF 转出 | 幻灯片、rebuttal、海报 |
| `.emf` | Inkscape 或 LibreOffice | Word；Visio 导入后取消组合 |

### 关于清晰度

位图**一律从 PDF 转出**，绝不直接从 SVG。因为 LibreOffice 的 PNG 过滤器会静默忽略 DPI 设置，只给你一张 96 dpi 的截图——请求 600 dpi 实际只出 317 px。所以 `render.py` 改成用支持密度参数的工具去栅格化 PDF，并且**回读实际像素数和 `--dpi` 对账**，转换器偷懒就报警：

```
png via pdftoppm @600 dpi -- 4200 x 1857 px
```

投稿用 **600 dpi**，做海报用 **1200 dpi**。

---

## 编辑输出：Visio、PowerPoint、Illustrator

`build/fig.vsdx` 里每个模块都是**真正的 Visio 形状**，带自己的 geometry、fill、line、character 段：

- 点一下方框，格式面板里显示填充色 `#FFE699`；
- 拖顶点，几何直接更新——不需要取消组合；
- 双击改字，仍然是 7 pt Times New Roman；
- 箭头是 `EndArrow=4`（实心三角）的折线，控制点可拖。

> **关于位图面板**：`image` 节点在 `.vsdx` 里导出为带标签的占位矩形，渲染报告会列出跳过的文件。想让图片自动嵌进去就用 `.pptx`，或者在 Visio 里用*插入 → 图片*手动放。

### 模块面板（stencil）

完全不想写 YAML？生成一个可拖拽的调色板：

```bash
python3 scripts/make_stencil.py -o build/stencil -f vsdx,pptx
```

<p align="center">
  <img src="assets/gallery/stencil.png" width="80%" alt="模块面板：全部形状 × 全部语义角色、9 组 tint 阶梯（带 hex）、全套线宽">
</p>

开在第二个窗口里，直接复制过来。复制过去的模块自带房屋样式的填充、描边、圆角和 7 pt Times 标签。

完整往返说明见 [`references/visio-workflow.md`](references/visio-workflow.md)。

---

## 审计器

```bash
python3 scripts/validate.py spec.yaml --svg build/fig.svg [--strict] [--json]
```

| 代码 | 级别 | 抓什么 |
|---|---|---|
| `text-too-small` | error | **最终印刷尺寸**下小于 5.5 pt 的文字 |
| `label-overflow` | error | 文字比框还宽 |
| `node-overlap` | error | 两个兄弟节点占同一块地方 |
| `inconsistent-role` | error | 同一个概念画成了两种颜色 |
| `bad-edge` | error | 边引用了不存在的节点 |
| `emoji` | error | emoji 或装饰字符 |
| `edge-crosses-node` | warning | 箭头从第三个模块身上穿过去 |
| `off-palette` | warning | 用了色板之外的颜色 |
| `too-many-hues` | warning | 超过 5 个色系 |
| `stroke-zoo` | warning | 超过 4 种不同线宽 |
| `mixed-fonts` | warning | 一张图里混用两种字体 |
| `label-verbose` | warning | 标签超过 6 个词 |
| `tall-figure` | warning | 超出该会场的高度预算 |
| `gradient` / `shadow` | warning | SVG 里有渐变或滤镜 |
| `unconnected` | note | 某个模块没有任何箭头连接 |

有 error 时退出码非零，加 `--strict` 时 warning 也会非零——可以直接挂进 CI 或 pre-commit。

它不是摆设。在一篇真实论文上，它抓出了 4 个 5.4 pt 的标签、一张用了 6 个色系的图、以及一个把 `encoder` 画成两种颜色的模板——这些本来都会被交出去。

审计器判断不了图**是否讲清楚了**。请渲染一张 PNG 亲眼看一遍。

---

## 放进论文里

引擎以**最终印刷磅值**排版，`venue` + `width` 会把画布设成该会场的精确栏宽。所以：

```latex
\begin{figure*}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/overview.pdf}
  \caption{\textbf{Overview of X.} <论断>。<从左到右的各个部件>。}
  \label{fig:overview}
\end{figure*}
```

就是 100% 呈现，spec 里的 `size: 7.0` 在纸上就是 7.0 pt。

想放到栏宽的 80%？在 **spec 里**设 `width_frac: 0.8`，LaTeX 那边保持 `width=\linewidth`。
写成 `width=0.8\linewidth` 会把字号一起缩到 5.6 pt。

| 会场 | `\columnwidth` | `\textwidth` |
|---|---|---|
| CVPR / ICCV / WACV | 237.13 pt | 496.85 pt |
| ECCV (LNCS) | 347.12 pt | 347.12 pt |
| NeurIPS / ICLR | 397.48 pt | 397.48 pt |
| ICML | 234.88 pt | 487.82 pt |
| AAAI | 238.49 pt | 504.00 pt |
| ACL / EMNLP | 219.08 pt | 455.24 pt |

浮动体摆放和 camera-ready 检查清单见
[`references/latex-integration.md`](references/latex-integration.md)。

### 让图可复现

```
figures/
  overview.pdf          <- LaTeX 引用的
  overview.pptx         <- 发给合作者改的
  src/overview.yaml     <- spec，进版本库
  src/crops/*.png       <- 真实数据截图
```

```bash
for f in figures/src/*.yaml; do
  python3 scripts/render.py "$f" -o "figures/$(basename "${f%.yaml}")" \
          -f svg,pdf,pptx --dpi 600
done
```

---

## 仓库结构

```
SKILL.md                  Claude Code 入口（带 frontmatter 路由）
AGENTS.md                 Codex / 其他 agent 入口
manifest.yaml             什么任务加载哪个片段
install.sh                一条命令装成 Claude Code skill

static/core/
  stance.md               不可妥协的规矩 + "AI 味"清单
  contract.md             动笔前必须回答的七个问题

references/
  house-style.md          量出来的配色/字号/线宽，以及测量方法本身
  spec-language.md        spec 完整语法
  archetypes.md           十一个原型，以及各自的成败关键
  case-studies.md         五篇论文的图逐张拆解
  anti-ai-checklist.md    自动审计项 + 人眼复核流程
  visio-workflow.md       Visio / PowerPoint / Illustrator 编辑
  latex-integration.md    尺寸换算、浮动体、camera-ready 检查

scripts/
  render.py               spec -> svg / pdf / png / tiff / emf / vsdx / pptx
  validate.py             审计器
  make_stencil.py         模块面板生成器
  cvprfig/                引擎（纯标准库）
    style.py              色板、字号、线宽、几何常量
    text.py               烘焙好的 Adobe Core-14 字宽 + 行内标记
    layout.py             盒模型求解器
    edges.py              正交路由
    shapes.py             形状词汇表
    svg.py vsdx.py pptx.py   同一套版面的三个渲染后端
    miniyaml.py           零依赖 YAML 子集解析器

templates/                十一个原型 + stencil.vsdx / stencil.pptx
examples/quickstart.yaml  上面那个 50 行示例
assets/gallery/           渲染预览
tests/test_engine.py      105 项回归测试
```

---

## 测试

```bash
python3 tests/test_engine.py
```

105 项检查，零依赖，约两秒。覆盖：字宽测量对照已发表论文的实际框宽、内置 YAML 解析器（与 PyYAML 输出逐字节一致）、版面吸附、端口法向路由、颜色与具名线宽解析、容器嵌套形式、每一种形状、十一个模板的渲染**并且通过审计**、`.vsdx` / `.pptx` 包结构与形状数量、审计器自身的正反例。

CI 在 Python 3.9 / 3.11 / 3.13 上**不装任何依赖**跑这些测试，所以一旦有人引入依赖，构建会直接失败。

---

## 常见问题

<details>
<summary><b>能画柱状图、曲线、热力图、消融实验图吗？</b></summary>

不能，而且它会明确告诉你。那些是 matplotlib/seaborn 的活。本项目专攻 matplotlib 不擅长的部分：架构图、pipeline、teaser、模块细节图、分类树。
</details>

<details>
<summary><b>用了图像生成模型吗？</b></summary>

没有。既不用扩散模型，也不让 LLM 直接写 SVG 坐标——这两条恰恰会产出本项目要消灭的那种通用感。所有坐标由确定性求解器算出，所以同一份 spec 永远得到同一张图，spec 的 diff 就是图的 diff。
</details>

<details>
<summary><b>它会编造我的实验结果吗？</b></summary>

不会。没有 `src` 的 `image` 节点会渲染成**故意很显眼**的带标签占位框，让未完成的图不可能被误当成完成品；渲染报告还会列出哪些槽位还空着。
</details>

<details>
<summary><b>图太宽了怎么办？</b></summary>

渲染器会整体缩放，并告诉你**实际生效**的字号：

```
WARNING: Layout is 539.6 pt wide but the target column is 504.0 pt,
         so the figure is scaled to 93%; body labels render at ~6.5 pt.
```

低于 5.5 pt 就升级成 error。正确的解法是缩短标签、砍掉一个阶段、或者拆成两张图——不是接受这个缩放。
</details>

<details>
<summary><b>改完 <code>.vsdx</code> 能反解回 spec 吗？</b></summary>

不能，没有反向解析器。建议在结构还在变的阶段以 spec 为准，等版面定稿之后再转去直接改 `.vsdx` / `.pptx`。
</details>

<details>
<summary><b>转换之后字体不对。</b></summary>

SVG 里写的是 `Times New Roman, Nimbus Roman, Liberation Serif, Times, serif`，会优雅降级，但转换器有自己的替换策略。用 `pdffonts build/fig.pdf` 检查；要求字形精确就用 Inkscape 加 `--export-text-to-path` 转。
</details>

<details>
<summary><b>怎么模仿某一篇论文的风格？</b></summary>

直接从它发表的 PDF 里把配色量出来——方法就在 [`references/house-style.md`](references/house-style.md) 开头；然后照着那些颜色写 spec。[`references/case-studies.md`](references/case-studies.md) 把五张知名论文图逐个手法拆开讲了。
</details>

<details>
<summary><b>两个东西同名但必须不同颜色。</b></summary>

通常正确的解法是把名字区分开——真实的 dual-branch 图会写 `encoder f_θ` 和 `encoder f_ξ`，而不是两个 `encoder`。如果这个对比确实就是重点，在节点上设 `same_label_ok: true` 单独关掉这一项检查。
</details>

---

## 参考语料与致谢

样式常量是从以下已发表论文 PDF 的矢量内容中测量得到的。只提取了排版参数——配色、字号、线宽、几何——**未复制任何图形内容**；`assets/gallery/` 里的全部示例均由本项目自己的模板渲染生成。

| 论文 | 会场 |
|---|---|
| SparseWorld: A Flexible, Adaptive and Efficient 4D Occupancy World Model | arXiv:2510.17482 |
| GaussianWorld: Gaussian World Model for Streaming 3D Occupancy Prediction | CVPR 2025, arXiv:2412.10373 |
| EmbodiedOcc: Embodied 3D Occupancy Prediction | arXiv:2412.04380 |
| StreamVGGT: Streaming Visual Geometry Transformer | arXiv:2507.11539 |
| TPVFormer: Tri-Perspective View for 3D Semantic Occupancy Prediction | CVPR 2023, arXiv:2302.07817 |

测量方法与完整数值见 [`references/house-style.md`](references/house-style.md)——你可以对任何一篇你欣赏其配图的论文重复这个过程。

---

## 参与贡献

欢迎 issue 和 PR。请确保 `python3 tests/test_engine.py` 通过，并且新增模板的审计器 **error 为零**——CI 两项都会检查。

特别欢迎：

- 本项目尚未覆盖领域的**新原型**（NLP、语音、强化学习、理论、机器人系统）；
- 用真实 `\the\columnwidth` 核实过的**会场栏宽**；
- 从其他实验室论文图中量出的**样式数据**。

## 许可

[MIT](LICENSE) © 2026 Zhao Liu。

可自由用于论文、商业用途和二次分发。除保留许可声明外无需署名——不过如果这些图帮到了你，欢迎给个 star 或提一句。
