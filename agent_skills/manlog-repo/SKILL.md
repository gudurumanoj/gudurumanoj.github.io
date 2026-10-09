---
name: manlog-repo
description: >-
  Full working context for the man'log repository (gudurumanoj.github.io): a Hugo + PaperMod
  personal site with a blog, deployed to GitHub Pages. Covers architecture, file map, build and
  deploy, conventions, known pitfalls, and the owner's preferences. Use when changing layouts,
  CSS, config, search, the landing page, nav, deployment, or debugging the site in this repo.
  For only writing or editing a blog post, use agent_skills/manlog-write-post/SKILL.md instead.
---

# man'log repository

Personal site of Manoj Guduru (GitHub `gudurumanoj`), live at https://gudurumanoj.github.io/.
Hugo extended **0.167.0**, theme **PaperMod** (git submodule), search by **Pagefind**, deployed
by GitHub Actions. Human-facing docs: `README.md` (architecture) and `WRITING.md` (authoring).
Read those only for detail not covered here. Agent skills live in `agent_skills/` (this file and
`manlog-write-post/SKILL.md`); `AGENTS.md` points to them. Update all three when conventions change.

## Owner's rules

- **Never commit, push, or create branches.** The owner does all git operations. Leave changes
  in the working tree and list them at the end.
- Light theme only: warm cream + terracotta palette modelled on posttrainbench.com. The dark toggle
  is disabled; don't reintroduce dark styling.
- The landing page is a personal intro only (no post cards, no blog pointers). Nav bar has only
  **Blog**. No CV/resume on the site.
- Don't invent facts about the owner (job, papers, affiliations). Use clearly marked placeholders.
- Keep `README.md` / `WRITING.md` in sync when behaviour changes.

## Commands

```bash
git clone --recurse-submodules <repo>       # theme is a submodule; or: git submodule update --init --recursive
hugo server -D                              # preview with drafts at http://localhost:1313
hugo -D --renderToMemory                    # fast validation build, writes nothing
hugo -D && npx -y pagefind --site public --output-path static/pagefind   # local search index (git-ignored)
```

On the owner's Linux box Hugo is at `~/.local/bin/hugo`. Two `WARN deprecated: .Language.*`
lines come from PaperMod and are harmless; anything else (math errors, missing files) is real.
Clean up `public/`, `resources/`, `.hugo_build.lock` after local builds (all git-ignored).

## File map

```
config/_default/
  hugo.toml      title, baseURL, theme, goldmark (unsafe HTML, passthrough math), pagination 12, taxonomies
  params.toml    PaperMod params at top; [manlog] section (name, tagline, avatar, socials, katexCSS, mermaidJS)
  menus.toml     nav bar ([[main]] blocks); currently only Blog
content/
  _index.md      landing page text
  search.md      /search/ (layout: pagefind);  archives.md  /archives/ (PaperMod layout)
  blog/_index.md             /blog/ title + description
  blog/<slug>/index.md       one post per folder (page bundle) with its images/demos; flat, no categories
layouts/                     man'log layer; overrides the theme
  home.html                  landing: avatar or monogram, name, tagline, socials, .Content
  blog/list.html, term.html  card grids + tag bar via _partials/manlog/listing.html
  pagefind.html              search page (Pagefind Component UI, faceted tag filter)
  _markup/render-passthrough.html        $..$/$$..$$ -> KaTeX HTML at build time (transform.ToMath)
  _markup/render-codeblock.html          every other ``` block -> <details class="ml-code"> panel
  _markup/render-codeblock-mermaid.html  ```mermaid -> <pre class="mermaid">
  _shortcodes/embed.html, video.html     iframe embeds (Claude artifacts), looping videos
  _partials/manlog/head-extras.html      the ONLY place CSS/JS is injected into <head>
  _partials/manlog/card.html, listing.html, pagination.html, icon.html
  _partials/extend_head.html, extend-head.html, head-additions.html, head/custom.html
                             one-line shims including head-extras under each theme's hook name
assets/css/manlog.css        all man'log styles (--ml-* vars mapped to theme vars), .ml-diagram SVG classes
assets/css/extended/palette.css   PaperMod colour overrides (cream/terracotta)
assets/js/toc-rail.js        right-side hover contents rail on posts
assets/js/mermaid-init.js    Mermaid loader + light palette themeVariables
assets/js/code-blocks.js     copy + show-all buttons for code panels
archetypes/blog.md           front matter for `hugo new blog/...`
static/                      favicons (Twemoji 🪵 log), site.webmanifest
pagefind.yml                 index only blog/**/index.html; exclude_selectors for UI chrome, katex, mermaid
.github/workflows/hugo.yml   build (HUGO_VERSION) + pagefind + deploy-pages on push to master
```

## How things work

- **Theme-agnostic layer**: our templates only fill the `main` block, and everything we add to
  `<head>` goes through `head-extras.html`. Swapping `theme` in `hugo.toml` should need only
  config changes (verified with Ananke).
- **Conditional assets**: render hooks set `.Page.Store` flags (`hasMath`, `hasMermaid`);
  `head-extras.html` calls `$noop := .WordCount` first to force content rendering, then loads
  KaTeX CSS / Mermaid only on pages that need them.
- **Code panels**: `render-codeblock.html` wraps Hugo's highlighted output in a collapsible
  `<details class="ml-code">` (header: label/title, line count, show all, copy; body capped at
  `--ml-code-max` with its own scroll). Sets `hasCode`, which loads `assets/js/code-blocks.js`.
  PaperMod copy buttons are off. Generic `.post-content details` card styles must keep
  `:not(.ml-code)`.
- **Page resources**: `[contentTypes]` lists only Markdown, so `.html` files in a post folder
  are plain resources (used by `{{< embed >}}`), not pages.
- **Cards**: cover = front matter `thumbnail`, else `cover.*` in the bundle (800x450 webp), else
  a generated tile coloured by a hash of the first tag.
- **Tag bar**: `listing.html` renders the chip row on `/blog/` and `/tags/<tag>/` from
  `site.Taxonomies.tags.ByCount` (top 15, then an "All N tags" link), so new tags need no config.
  Posts are deliberately flat (no category folders): URLs are `/blog/<slug>/` and must stay stable;
  use front matter `aliases` if a slug ever changes.
- **TOC rail**: `toc-rail.js` builds ticks from h2/h3 with ids; shown on blog posts with at
  least `[manlog].tocMinHeadings` (3) headings unless front matter `toc: false`.
- **Search**: Pagefind runs after Hugo (CI and locally). Filters come from
  `<meta data-pagefind-filter="tag[content]" ...>` emitted in head-extras for blog posts.
  Multi-select within a filter is AND. Ctrl/Cmd+K and any `[data-ml-search]` element open a
  `<pagefind-modal>`; the blog page has a Search button.
- **Diagrams**: Mermaid for auto-layout; hand-written inline SVG in `<figure class="ml-diagram">`
  with CSS classes (`box violet|green|blue|rose|sand`, `group`, `name`, `note`, `label`,
  `arrow [both|dashed|plain]`) when layout matters. Template in `WRITING.md`.

## Pitfalls (each one has bitten this repo)

- **TOML ordering**: in `params.toml`, plain keys must precede the first `[table]`. Keys placed
  after `[[manlog.socials]]` silently become part of that table. Keep socials last.
- **KaTeX version**: Hugo bundles KaTeX (0.18.4 in Hugo 0.166-0.167). `katexCSS` must be the
  same version or equations render wrongly. Re-check when bumping `HUGO_VERSION`.
- **Hugo layout names**: this is the new (0.146+) structure: `_partials`, `_shortcodes`,
  `_markup`, `home.html`, `term.html`. Don't create `layouts/partials/` etc.
- **Raw HTML blocks in Markdown end at a blank line**: no blank lines inside `<svg>`/`<figure>`.
- **PaperMod `.md-content figure > figcaption`** is bold/16px; override with matching specificity.
- **Pagefind**: use the `tag[content]` meta syntax (plain `data-pagefind-filter` on a meta
  yields 0 filters); glob must stay `index.html` so demo HTML files aren't indexed.
- `pkill -f "<pattern>"` can match the invoking shell itself; kill by PID instead.

## Verifying UI changes

Build with drafts, serve `public/` (`python3 -m http.server 1414 --bind 127.0.0.1`), and check
pages in a headless browser (Playwright Chromium works; take screenshots of `/`, `/blog/`, the
feature-tour post, and `/search/`). The feature-tour post
(`content/blog/manlog-feature-tour/index.md`) exercises every feature: math,
Mermaid, SVG diagram, embed, GIF, code, TOC rail. Stop the server and delete build output after.
