---
title: "A Tour of man'log: Everything a Post Can Do"
date: 2026-10-07T09:00:00+05:30
draft: false
tags: ["building-block", "meta"]
summary: "A reference post that exercises every feature of this blog: images, GIFs, code, LaTeX math, Mermaid diagrams, embedded interactive demos, and the contents rail on the right."
aliases: ["/blog/building-blocks/manlog-feature-tour/"]
---

This post is both a demo and a cheat sheet. Open
[its source](https://github.com/gudurumanoj/gudurumanoj.github.io/blob/master/content/blog/manlog-feature-tour/index.md)
side by side with the rendered page to see how each piece is written. Hover over the
ticks on the right edge of the screen to jump between sections.

## Text and formatting

Regular Markdown works as expected: **bold**, *italic*, `inline code`,
[links](https://gohugo.io/), and footnotes.[^1]

> Block quotes are good for definitions or a quote from a paper.

- Bullet lists
- with several items
  - and nesting

1. Numbered lists
2. work too

| Model | Params | Notes |
|-------|-------:|-------|
| Small | 125M   | fits on a laptop |
| Large | 70B    | needs a cluster  |

<details>
<summary>Click to expand a collapsible section</summary>

Raw HTML is allowed, so `<details>` works for long proofs or optional asides.

</details>

## Images and GIFs

Images live in the same folder as the post and are referenced by file name:

![A figure stored next to this post](figure.png "Optional caption shown on hover")

For a caption under the image, use Hugo's built-in `figure` shortcode:

{{< figure src="figure.png" caption="Figure 1. Same image with a visible caption." width="70%" >}}

GIFs are just images:

![Animated GIF](loading.gif)

For longer animations, an MP4 is far smaller than a GIF. The `video` shortcode plays it
looped and muted, like a GIF: `{{</* video src="clip.mp4" caption="..." */>}}`.

## Code and commands

Fenced code blocks get syntax highlighting and a copy button:

```python
import torch

def softmax(x: torch.Tensor, dim: int = -1) -> torch.Tensor:
    x = x - x.max(dim=dim, keepdim=True).values  # numerical stability
    return x.exp() / x.exp().sum(dim=dim, keepdim=True)
```

```bash
hugo new blog/ml/my-new-post/index.md
hugo server -D
```

## Math

Inline math uses single dollars, like $e^{i\pi} + 1 = 0$, or `\( ... \)`.
Display math uses double dollars or `\[ ... \]`:

$$
\mathrm{softmax}(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}
$$

\[
\mathcal{L}(\theta) = -\mathbb{E}_{(x,y)\sim\mathcal{D}}\left[\log p_\theta(y \mid x)\right]
\]

Aligned equations work too:

$$
\begin{aligned}
\nabla_\theta \mathcal{L} &= \mathbb{E}\left[\nabla_\theta \log p_\theta(y\mid x)\right] \\
\theta_{t+1} &= \theta_t - \eta \, \nabla_\theta \mathcal{L}
\end{aligned}
$$

Math is rendered to HTML when the site is built, so pages load fast and nothing flickers.

### Writing a literal dollar sign

To show a dollar sign as plain text, escape it with a backslash: \$5 per GPU-hour.

## Diagrams with Mermaid

Write a fenced block with the language set to `mermaid`:

```mermaid
flowchart LR
  data[Dataset] --> tok[Tokenizer]
  tok --> model[Transformer]
  model --> loss[Cross-entropy loss]
  loss -->|backprop| model
```

```mermaid
sequenceDiagram
  participant U as User
  participant S as Server
  U->>S: request
  S-->>U: response
```

Diagrams are drawn in the site's colours.

## Custom diagrams with SVG

Mermaid places boxes automatically. When the layout matters, write an SVG directly in the
post: each box, label and arrow sits exactly where you put it. Styles such as `box violet`,
`name`, `note` and `arrow` come from the site's CSS, so only coordinates and text go here.

<figure class="ml-diagram">
<svg viewBox="0 0 860 330" role="img" aria-label="Crawler worker: parser, link extractor and URL filter feeding shared stores">
  <defs><marker id="ml-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="group" x="20" y="10" width="820" height="160" rx="14"/>
  <text class="label" x="430" y="40">One worker process: stateless, per page</text>
  <rect class="box violet" x="45" y="62" width="220" height="80" rx="8"/>
  <text class="name" x="155" y="96">Content parser</text>
  <text class="note violet" x="155" y="120">Parse HTML</text>
  <rect class="box violet" x="320" y="62" width="220" height="80" rx="8"/>
  <text class="name" x="430" y="96">Link extractor</text>
  <text class="note violet" x="430" y="120">Find, normalize</text>
  <rect class="box violet" x="595" y="62" width="220" height="80" rx="8"/>
  <text class="name" x="705" y="96">URL filter</text>
  <text class="note violet" x="705" y="120">Cheap rules</text>
  <rect class="box green" x="45" y="235" width="220" height="80" rx="8"/>
  <text class="name" x="155" y="269">Content seen?</text>
  <text class="note green" x="155" y="293">Shared store</text>
  <rect class="box sand" x="320" y="235" width="220" height="80" rx="8"/>
  <text class="name" x="430" y="269">URL frontier</text>
  <text class="note" x="430" y="293">Queues</text>
  <rect class="box green" x="595" y="235" width="220" height="80" rx="8"/>
  <text class="name" x="705" y="269">URL seen?</text>
  <text class="note green" x="705" y="293">Shared, billions</text>
  <line class="arrow" x1="268" y1="102" x2="316" y2="102"/>
  <line class="arrow" x1="543" y1="102" x2="591" y2="102"/>
  <line class="arrow" x1="155" y1="145" x2="155" y2="231"/>
  <line class="arrow" x1="705" y1="145" x2="705" y2="231"/>
  <line class="arrow" x1="592" y1="275" x2="544" y2="275"/>
</svg>
<figcaption>A web crawler's worker pipeline, drawn as SVG in the Markdown.</figcaption>
</figure>

## Interactive demos

Any self-contained HTML file in the post folder can be embedded. This is how to include
a Claude artifact: ask Claude to export the artifact as a single standalone HTML file,
save it next to the post, and embed it:

{{< embed src="demo.html" height="420" caption="Gradient descent on a 2D bowl. Click anywhere to restart from that point." >}}

## Callouts and long sections

### A subsection

Subsections (`###`) show up as shorter ticks in the contents rail and are indented in
the hover panel.

### Another subsection

Posts with fewer than three headings don't show the rail. To hide it on a specific
post, set `toc: false` in the front matter.

## Wrapping up

That covers the building blocks. See `WRITING.md` in the repository for the full guide.

[^1]: Footnotes are collected at the bottom of the post.
