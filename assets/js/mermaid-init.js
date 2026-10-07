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
  mermaid.initialize(
    isDark()
      ? { startOnLoad: false, theme: "dark" }
      : {
          startOnLoad: false,
          theme: "base",
          themeVariables: {
            background: "#faf8f3",
            primaryColor: "#f3f0e8",
            primaryBorderColor: "#a66b4f",
            primaryTextColor: "#2d2a23",
            secondaryColor: "#e8e4d9",
            tertiaryColor: "#fdfcf8",
            lineColor: "#6b655a",
            textColor: "#2d2a23",
            noteBkgColor: "#f3e6d8",
            noteBorderColor: "#a66b4f",
            actorBkg: "#f3f0e8",
            actorBorder: "#a66b4f",
            signalColor: "#2d2a23",
            fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif",
          },
        }
  );
  await mermaid.run({ nodes });
}

render();

// Re-render when the theme's light/dark toggle flips <html data-theme>.
new MutationObserver(render).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["data-theme"],
});
