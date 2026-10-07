# Writing for man'log

How to add posts and everything that goes in them, organise them with categories and tags,
and change the landing page and nav bar. For how the repo is built, see [README.md](README.md).

The post [A Tour of man'log](content/blog/building-blocks/manlog-feature-tour/index.md) uses
every feature below. Keep it open as a live example.

## Quick start

```bash
hugo new blog/ml/attention-from-scratch/index.md   # creates the post from archetypes/blog.md
hugo server -D                                     # preview at http://localhost:1313
```

Write the post, set `draft: false`, commit and push. GitHub Actions publishes it in a minute
or two.

## Where posts live

Every post is a folder (a "page bundle") inside a category folder:

```
content/blog/
├── _index.md                       # the /blog/ page title and description
├── ml/
│   ├── _index.md                   # the ML category: title, description, order
│   └── attention-from-scratch/     # one post = one folder; the folder name is the URL slug
│       ├── index.md                # the post itself
│       ├── cover.png               # optional card image (picked up automatically)
│       ├── fig-attention.png       # images, GIFs, videos, HTML demos used by the post
│       └── demo.html
└── math/ ...
```

URL of that post: `/blog/ml/attention-from-scratch/`.

Rules:
- The post file must be named `index.md`, inside its own folder.
- The folder name becomes the URL, so use lowercase words with hyphens.
- Put the post's files in the same folder and refer to them by file name.

## Front matter

The block between `---` lines at the top of `index.md`:

```yaml
---
title: "Attention From Scratch"        # required
date: 2026-10-07T09:00:00+05:30        # required; sets ordering (newest first)
draft: true                            # required; set to false to publish
tags: ["ml", "building-block"]         # optional, but recommended
summary: "One or two sentences shown on the card and in search results."  # recommended
thumbnail: diagram.png                 # optional; overrides the automatic cover.* lookup
toc: false                             # optional; hides the right-side contents rail
description: "Short subtitle shown under the title on the post page."      # optional
---
```

| Field | Required | Effect |
|-------|----------|--------|
| `title` | yes | Post title, card title, browser tab title |
| `date` | yes | Sorting and the date on cards. A future date stays hidden until then |
| `draft` | yes | `true` = only visible with `hugo server -D`; never published |
| `tags` | no | Chips on the card; creates `/tags/<tag>/`; search filter |
| `summary` | no | Card text and search excerpt. Without it, the first ~40 words are used |
| `thumbnail` | no | Card image file in the post folder. Default: any `cover.*` file, else a generated tile |
| `toc` | no | `false` hides the contents rail. It shows automatically on posts with 3+ `##`/`###` headings |
| `description` | no | Subtitle under the post title |

## Tags

Use lowercase, hyphenated tags and reuse existing ones so the filters stay useful:

| Tag | Use for |
|-----|---------|
| `building-block` | Self-contained explainers of a core idea |
| `ml` | Machine learning |
| `math` | Math |
| `cp` | Competitive programming |
| `random-thoughts` | Opinions, musings, half-baked ideas |

Add new tags freely: writing a new tag in a post's front matter is all it takes to create it.
The tag pages and search filters appear on the next build.

**Categories vs tags**: the folder is the category (one per post, shown as a chip row on
`/blog/`); tags are many per post and cut across categories.

A post with several tags shows up on each of those tag pages (`/tags/ml/`, `/tags/math/`, ...)
and shows all its tags as chips on its card. On `/search/`, the **Tags** filter lists every tag
with a post count and works without typing a query. Ticking several tags narrows the results
to posts that have **all** of them; options that would give zero results are hidden.

## Images, GIFs and video

```markdown
![Alt text describing the image](fig-attention.png)

![Alt text](fig-attention.png "Tooltip shown on hover")
```

For a visible caption or a custom width, use Hugo's built-in `figure` shortcode:

```markdown
{{< figure src="fig-attention.png" caption="Figure 1. Scaled dot-product attention." width="70%" >}}
```

GIFs work exactly like images. For anything longer than a few seconds, export an MP4 instead
(it's usually 5-10x smaller) and use:

```markdown
{{< video src="training.mp4" caption="Loss over training" >}}           <!-- loops silently, like a GIF -->
{{< video src="talk.mp4" controls="true" >}}                            <!-- normal player -->
```

**Card cover**: drop a `cover.png` (or `.jpg`/`.webp`) into the post folder. A 16:9 image of
at least 1200x675 looks best; it is cropped and resized automatically. Without one, the card
shows a coloured tile with the title.

## Code and commands

Use fenced code blocks with a language for syntax highlighting. A copy button appears on hover.

````markdown
```python
def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()
```

```bash
pip install torch
```
````

## Math (LaTeX)

| You write | Result |
|-----------|--------|
| `$x^2$` or `\(x^2\)` | inline math |
| `$$ ... $$` or `\[ ... \]` on their own lines | display (centred) math |

```markdown
The softmax of $z$ is

$$
\sigma(z)_i = \frac{e^{z_i}}{\sum_j e^{z_j}}
$$

$$
\begin{aligned}
a &= b + c \\
d &= e
\end{aligned}
$$
```

- Math is rendered when the site is built, so a typo shows up as a **warning in the
  `hugo server` output** and the formula appears in red on the page.
- To write a literal dollar sign, escape it: `\$5`.
- Anything KaTeX supports works: `\mathbb`, `\operatorname`, `aligned`, `cases`, `pmatrix`,
  and more ([full list](https://katex.org/docs/supported.html)).

## Diagrams (Mermaid)

````markdown
```mermaid
flowchart LR
  A[Input] --> B[Model]
  B --> C[Loss]
```
````

Any Mermaid diagram type works (flowchart, sequence, class, state, gantt, pie, and more). See the
[Mermaid docs](https://mermaid.js.org/intro/). Diagrams use the site palette (set in `assets/js/mermaid-init.js`).

Mermaid chooses the layout itself. That is fine for most flowcharts, but it sometimes rearranges
boxes or bends arrows in ways you didn't want. When the exact layout matters, draw the diagram
in SVG instead (next section).

## Custom diagrams (SVG)

Any SVG pasted into a post is drawn in place, so you can position every box and arrow exactly.
The site's CSS supplies the colours and fonts, so a diagram is only coordinates and text. Copy
this template:

```html
<figure class="ml-diagram">
<svg viewBox="0 0 860 230" role="img" aria-label="Describe the diagram for screen readers">
  <defs><marker id="ml-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="group" x="20" y="10" width="540" height="160" rx="14"/>
  <text class="label" x="290" y="40">A dashed group with a label</text>
  <rect class="box violet" x="45" y="62" width="220" height="80" rx="8"/>
  <text class="name" x="155" y="96">First step</text>
  <text class="note violet" x="155" y="120">What it does</text>
  <rect class="box violet" x="320" y="62" width="220" height="80" rx="8"/>
  <text class="name" x="430" y="96">Second step</text>
  <text class="note violet" x="430" y="120">What it does</text>
  <rect class="box green" x="595" y="62" width="220" height="80" rx="8"/>
  <text class="name" x="705" y="96">Storage</text>
  <text class="note green" x="705" y="120">Shared</text>
  <line class="arrow" x1="268" y1="102" x2="316" y2="102"/>
  <line class="arrow" x1="543" y1="102" x2="591" y2="102"/>
  <path class="arrow dashed" d="M155,145 V220 H705 V145"/>
</svg>
<figcaption>Optional caption.</figcaption>
</figure>
```

**Coordinates.** `viewBox="0 0 W H"` sets the drawing area. The SVG always stretches to the
post width and scales down on phones, so only the proportions matter. `(0,0)` is the top-left
corner and `y` grows downward. A box at `x, y` with size `w × h` has its centre at
`x + w/2, y + h/2`. Put a box's text at its centre `x`: the `name` line about 34 units below
the box's top and the `note` line about 58 units below. The three-column grid above (boxes 220
wide at `x` = 45, 320, 595) fits most diagrams. For a lower row, add 150–170 to `y`.

**Classes.**

| Element | Class | Look |
|---------|-------|------|
| `<rect>` | `box violet`, `box green`, `box blue`, `box rose`, `box sand` | Filled box with a matching border (`box` alone is neutral) |
| `<rect>` | `group` | Dashed outline for grouping boxes |
| `<text>` | `name` | Bold box title |
| `<text>` | `note` plus a colour | Smaller, muted second line in the box's colour |
| `<text>` | `label` | Muted label for groups or arrows. Add `left` to left-align any text |
| `<line>` / `<path>` | `arrow` | Arrow with a head at the end. Add `both` for two heads, `dashed` for a dashed line, `plain` for no head |

Straight arrows are `<line x1 y1 x2 y2>`. For elbows, use a `<path>`: `d="M x,y V y2 H x2"` moves
to a start point, goes vertically to `y2`, then horizontally to `x2`. End arrows about 4 units
short of the box edge so the head doesn't overlap the border.

**Rules.**

- **No blank lines anywhere between `<figure>` and `</figure>`.** A blank line ends the HTML
  block, and the rest is printed as text.
- Keep the `<defs>` line in every diagram, because the arrowheads come from it. Two diagrams on
  one page can both use `id="ml-arrow"`.
- Text inside the SVG is real text, so it is searchable and stays sharp at any zoom.

**Let Claude draw it.** Give Claude a sketch, a screenshot, or a description, plus this template,
and ask: *"Recreate this diagram as SVG in exactly this format, using only these classes, with
no blank lines."* Paste the result into the post. The feature-tour post has a full example
(`content/blog/building-blocks/manlog-feature-tour/index.md`).

## Interactive demos and Claude artifacts

Any self-contained HTML page can be embedded in a post:

1. In Claude, ask: *"Export this artifact as a single, self-contained HTML file (inline all
   JS/CSS, load libraries from a CDN)."* For React artifacts, Claude can produce an HTML file
   that loads React from a CDN.
2. Save it into the post folder, e.g. `demo.html`.
3. Embed it:

```markdown
{{< embed src="demo.html" height="480" caption="Drag the slider to change the learning rate." >}}
```

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `src` | required | File in the post folder, or a full URL |
| `height` | `480` | Height in pixels |
| `caption` | none | Text under the demo (Markdown allowed) |
| `title` | caption | Accessible title for screen readers |

An "Open full screen" link is shown under every embed. External URLs work too, but many sites
(including claude.ai share links) refuse to be embedded, so saving the file locally is the
reliable route.

## Other handy bits

```markdown
Footnotes work.[^1]

[^1]: Like this.

> Block quotes for definitions or quotations.

<details>
<summary>Click to expand</summary>

Long proofs or optional detail. Leave a blank line after <summary>.

</details>
```

Tables use standard Markdown pipes. Raw HTML is allowed anywhere.

## Headings and the contents rail

- Start sections at `##`. The post title is the only `#`.
- `##` and `###` headings appear in the rail on the right (longer ticks for `##`); hovering it
  lists them, and clicking jumps there. On phones it becomes a "Contents" button at the
  bottom left.
- It appears when a post has at least 3 such headings (`tocMinHeadings` in
  `config/_default/params.toml`), and can be turned off per post with `toc: false`.

## Categories

To add a category, create a folder with an `_index.md`:

```bash
mkdir -p content/blog/systems
```

```yaml
# content/blog/systems/_index.md
---
title: "Systems"
description: "Distributed systems, GPUs, and performance."
weight: 50          # chip order on /blog/ (lower = further left)
---
```

It appears as a chip on `/blog/` and gets its own page at `/blog/systems/`. Categories can be
nested (`content/blog/ml/transformers/_index.md`); posts in sub-folders still appear on
`/blog/` and on every parent category page.

## The landing page

The home page is about you, not the blog. At the top it shows your name, an optional one-line
tagline, a photo or monogram, and social icons. Below that comes whatever you write in
`content/_index.md`.

- **Text**: edit `content/_index.md` (normal Markdown). `##` headings become small section
  titles.
- **Name, tagline, photo, social links**: edit the `[manlog]` section of
  `config/_default/params.toml`. For a photo, put a square image at
  `static/images/avatar.jpg` and set `avatar = "images/avatar.jpg"`.
- **Social icons available**: `github`, `x`, `linkedin`, `email`, `scholar`, `rss`, `link`.

```toml
[[manlog.socials]]
  name = "Email"
  url = "mailto:you@example.com"
  icon = "email"
```

A typical academic-style layout for `content/_index.md` (keep the sections you need):

```markdown
Hi, I'm Manoj. Two or three sentences: what you work on, where, and what you care about.

## Currently

Working on ... at [Place](https://...). Previously ... at ....

## Interests

Large-scale training, numerical methods, ...

## Publications

- **Paper title.** A. Author, **M. Guduru**, B. Author. *Venue* 2026.
  [paper](https://arxiv.org/abs/...) · [code](https://github.com/...)

## News

- **Oct 2026**: Something happened.
```

## The nav bar

Items come from `config/_default/menus.toml`. Lower `weight` = further left. Right now
it only has **Blog**. Tags, the archive and search still work: they're reached from the blog
page (tag chips, the search button, Ctrl/Cmd+K) or directly at `/tags/`, `/archives/` and
`/search/`. Add them back with `[[main]]` blocks if you want them in the bar.

**Link to an existing page or an external site**:

```toml
[[main]]
  name = "CV"
  url = "/cv.pdf"          # file placed at static/cv.pdf
  weight = 60

[[main]]
  name = "GitHub"
  url = "https://github.com/gudurumanoj"
  weight = 70
```

**Add a new top-level section** (e.g. `/projects/`):

1. Create `content/projects/_index.md`:
   ```yaml
   ---
   title: "Projects"
   description: "Things I've built."
   ---
   ```
2. Add pages as `content/projects/<name>/index.md`, with the same front matter as posts.
3. Add the menu entry:
   ```toml
   [[main]]
     name = "Projects"
     url = "/projects/"
     weight = 15
   ```

By default the section uses the theme's plain list. To give it the same card grid as the blog,
create `layouts/projects/list.html` containing:

```go-html-template
{{- define "main" }}
{{- partial "manlog/listing.html" (dict "page" . "pages" .RegularPagesRecursive) }}
{{- end }}
```

**A single standalone page** (like Now or Talks): create `content/now.md` with a `title`, write
Markdown below it, and add a `[[main]]` entry with `url = "/now/"`.

To remove an item, delete its `[[main]]` block.

## Publishing checklist

1. `draft: false`, and the `date` is not in the future.
2. `hugo server -D` shows no warnings for the post (math errors are reported here).
3. Images and demos load, and the card looks right on `/blog/`.
4. Commit and push. Check the **Actions** tab if the site doesn't update within a few minutes.

## The sample content

The repo ships with one published post (the feature tour) and three short **drafts**
(`ml/softmax-numerical-stability`, `cp/prefix-sums`, `thoughts/why-keep-a-log`) that exist to
fill the grid while previewing. Delete or rewrite them whenever you like; the drafts never
appear on the live site.
