// Markdown footnotes ([^1]) as side notes: on wide screens each note is copied into the right
// margin, level with its reference, and the footnote list at the bottom is hidden. Below the
// breakpoint (must match the wide-post media query in manlog.css) the bottom list is used.
(() => {
  const content = document.querySelector(".post-content");
  if (!content || !content.querySelector(".footnotes")) return;

  const wide = window.matchMedia("(min-width: 1200px)");
  const notes = [];

  content.querySelectorAll("a.footnote-ref").forEach((ref) => {
    const item = document.getElementById(decodeURIComponent(ref.hash.slice(1)));
    if (!item || notes.some((n) => n.item === item)) return;

    const note = document.createElement("aside");
    note.className = "ml-sidenote";
    const num = document.createElement("span");
    num.className = "ml-sidenote-num";
    num.textContent = ref.textContent;
    const body = document.createElement("div");
    body.append(...item.cloneNode(true).childNodes);
    body.querySelectorAll(".footnote-backref").forEach((a) => a.remove());
    note.append(num, body);
    content.append(note);
    notes.push({ ref, item, note });

    ref.addEventListener("mouseenter", () => note.classList.add("is-active"));
    ref.addEventListener("mouseleave", () => note.classList.remove("is-active"));
    ref.addEventListener("click", (e) => {
      if (!wide.matches) return;
      e.preventDefault();
      note.classList.add("is-active");
      setTimeout(() => note.classList.remove("is-active"), 1500);
    });
  });

  // Each note starts at its reference's line, pushed down if the previous note is still there.
  const layout = () => {
    content.classList.toggle("ml-has-sidenotes", wide.matches);
    if (!wide.matches) return;
    const origin = content.getBoundingClientRect().top;
    let floor = 0;
    notes.forEach(({ ref, note }) => {
      const top = Math.max(ref.getBoundingClientRect().top - origin - 3, floor);
      note.style.top = `${top}px`;
      floor = top + note.offsetHeight + 14;
    });
  };

  wide.addEventListener("change", layout);
  new ResizeObserver(layout).observe(content);
  window.addEventListener("load", layout);
  layout();
})();
