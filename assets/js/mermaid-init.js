import mermaid from "{{ site.Params.manlog.mermaidJS }}";

const nodes = [...document.querySelectorAll("pre.mermaid")];
nodes.forEach((n) => (n.dataset.source = n.textContent));

const isDark = () => {
  const t = document.documentElement.dataset.theme;
  if (t) return t === "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
};

async function render() {
  nodes.forEach((n) => {
    n.removeAttribute("data-processed");
    n.textContent = n.dataset.source;
  });
  mermaid.initialize({ startOnLoad: false, theme: isDark() ? "dark" : "default" });
  await mermaid.run({ nodes });
}

render();

// Re-render when the theme's light/dark toggle flips <html data-theme>.
new MutationObserver(render).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["data-theme"],
});
