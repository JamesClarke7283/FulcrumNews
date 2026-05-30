// Progressive enhancement for the story-detail tabs.
// Without JS, all panels render stacked (fully readable). With JS, they become tabs.
(function () {
  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-tab]"));
    var panels = Array.prototype.slice.call(root.querySelectorAll("[data-panel]"));
    if (!tabs.length) return;

    function activate(name) {
      panels.forEach(function (p) {
        p.hidden = p.getAttribute("data-panel") !== name;
        // the no-JS divider styling is unwanted once tabbed
        p.classList.remove("js-tab-divider", "mt-6", "border-t", "border-neutral-100", "pt-6");
      });
      tabs.forEach(function (t) {
        var on = t.getAttribute("data-tab") === name;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.classList.toggle("bg-white", on);
        t.classList.toggle("text-brand-600", on);
        t.classList.toggle("border-b-2", on);
        t.classList.toggle("border-brand-600", on);
      });
    }

    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        activate(t.getAttribute("data-tab"));
      });
    });
    activate(tabs[0].getAttribute("data-tab"));
  });
})();
