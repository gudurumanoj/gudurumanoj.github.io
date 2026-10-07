// Right-side table-of-contents rail: one tick per h2/h3, the active section is
// highlighted, hovering shows the heading list. Built from the rendered page so
// it does not depend on the theme's templates.
(() => {
  const script = document.currentScript;
  const minHeadings = parseInt(script?.dataset.minHeadings || "3", 10);

  const ROOT_SELECTORS = [".post-content", ".article-content", ".article-page", "article", "main"];
  const root = ROOT_SELECTORS.map((s) => document.querySelector(s)).find(
    (el) => el && el.querySelector("h2[id], h3[id]")
  );
  if (!root) return;

  const headings = [...root.querySelectorAll("h2[id], h3[id]")].filter(
    (h) => !h.closest(".ml-card, .footnotes, figure")
  );
  if (headings.length < minHeadings) return;

  const label = (h) => {
    const clone = h.cloneNode(true);
    clone.querySelectorAll(".anchor, .hanchor, .heading-anchor").forEach((a) => a.remove());
    return clone.textContent.replace(/#\s*$/, "").trim();
  };

  const nav = document.createElement("nav");
  nav.className = "ml-toc";
  nav.setAttribute("aria-label", "Table of contents");

  const rail = document.createElement("div");
  rail.className = "ml-toc-rail";
  rail.setAttribute("aria-hidden", "true");

  const panel = document.createElement("div");
  panel.className = "ml-toc-panel";
  const list = document.createElement("ol");
  panel.append(list);

  const toggle = document.createElement("button");
  toggle.className = "ml-toc-toggle";
  toggle.type = "button";
  toggle.textContent = "Contents";
  toggle.setAttribute("aria-expanded", "false");

  const ticks = [];
  const links = [];
  headings.forEach((h) => {
    const level = h.tagName === "H2" ? 2 : 3;

    const tick = document.createElement("a");
    tick.className = `ml-toc-tick lvl${level}`;
    tick.href = `#${h.id}`;
    tick.tabIndex = -1;
    rail.append(tick);
    ticks.push(tick);

    const li = document.createElement("li");
    li.className = `lvl${level}`;
    const a = document.createElement("a");
    a.href = `#${h.id}`;
    a.textContent = label(h);
    li.append(a);
    list.append(li);
    links.push(a);
  });

  // Keep the rail within ~60% of the viewport even for very long posts.
  const fitRail = () => {
    const spacing = Math.max(3, Math.min(10, (window.innerHeight * 0.6) / headings.length - 2));
    rail.style.setProperty("--ml-tick-gap", `${spacing}px`);
  };
  fitRail();
  window.addEventListener("resize", fitRail);

  nav.append(rail, panel, toggle);
  document.body.append(nav);

  let active = -1;
  const setActive = (i) => {
    if (i === active) return;
    if (active >= 0) {
      ticks[active].classList.remove("active");
      links[active].classList.remove("active");
    }
    active = i;
    if (i < 0) return;
    ticks[i].classList.add("active");
    links[i].classList.add("active");
    if (nav.matches(":hover, .open")) return;
    const top = links[i].offsetTop - panel.clientHeight / 2;
    panel.scrollTop = Math.max(0, top);
  };

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const line = window.innerHeight * 0.3;
      let idx = -1;
      for (let i = 0; i < headings.length; i++) {
        if (headings[i].getBoundingClientRect().top <= line) idx = i;
        else break;
      }
      setActive(idx === -1 ? 0 : idx);
      ticking = false;
    });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  nav.addEventListener("click", (e) => {
    const a = e.target.closest("a[href^='#']");
    if (!a) return;
    const target = document.getElementById(decodeURIComponent(a.hash.slice(1)));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    history.replaceState(null, "", a.hash);
    nav.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  });

  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", (e) => {
    if (!nav.contains(e.target)) {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
})();
