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

// Tab groups from layouts/_shortcodes/tabs.html: one button per code panel, one panel visible.
for (const group of document.querySelectorAll(".ml-tabs")) {
  const panels = [...group.querySelectorAll(":scope > .ml-code")];
  if (panels.length < 2) continue;

  const bar = Object.assign(document.createElement("div"), { className: "ml-tabs-bar" });
  bar.setAttribute("role", "tablist");
  const tabs = panels.map((panel, i) => {
    const tab = Object.assign(document.createElement("button"), {
      type: "button",
      className: "ml-tab",
      textContent: panel.querySelector(".ml-code-label").textContent,
    });
    tab.setAttribute("role", "tab");
    tab.addEventListener("click", () => select(i));
    tab.addEventListener("keydown", (e) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (!step) return;
      const next = (i + step + tabs.length) % tabs.length;
      select(next);
      tabs[next].focus();
    });
    bar.append(tab);
    return tab;
  });

  // Hidden panels report zero height, so "show all" is re-evaluated when one becomes visible.
  const select = (i) => {
    panels.forEach((panel, j) => {
      panel.hidden = j !== i;
      tabs[j].setAttribute("aria-selected", String(j === i));
      tabs[j].tabIndex = j === i ? 0 : -1;
    });
    panels[i].dispatchEvent(new Event("toggle"));
  };

  group.prepend(bar);
  group.classList.add("is-tabbed");
  select(0);
}
