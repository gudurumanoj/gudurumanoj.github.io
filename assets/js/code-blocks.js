// Code panels from layouts/_markup/render-codeblock.html: "show all" for bodies taller than the
// height cap, and a copy button. Buttons sit inside <summary>, so clicks must not toggle <details>.
for (const panel of document.querySelectorAll(".ml-code")) {
  const body = panel.querySelector(".ml-code-body");
  const expand = panel.querySelector("[data-ml-expand]");
  const copy = panel.querySelector("[data-ml-copy]");

  const refresh = () => {
    const expanded = panel.classList.contains("is-expanded");
    expand.textContent = expanded ? "− collapse" : "+ show all";
    expand.hidden = !panel.open || (!expanded && body.scrollHeight <= body.clientHeight + 2);
  };

  expand.addEventListener("click", (e) => {
    e.preventDefault();
    panel.classList.toggle("is-expanded");
    refresh();
    if (!panel.classList.contains("is-expanded") && panel.getBoundingClientRect().top < 0) {
      panel.scrollIntoView({ block: "start" });
    }
  });

  copy.hidden = false;
  copy.addEventListener("click", async (e) => {
    e.preventDefault();
    const text = body.querySelector("code")?.innerText ?? body.innerText;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const area = Object.assign(document.createElement("textarea"), { value: text });
      document.body.append(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    copy.textContent = "copied";
    setTimeout(() => (copy.textContent = "copy"), 1500);
  });

  panel.addEventListener("toggle", refresh);
  refresh();
}
