// Theme switcher. The initial theme is set by an inline script in <head> (no FOUC).
// This wires the toggle button and keeps following the OS until the user chooses.
(function () {
  var root = document.documentElement;

  function apply(dark) {
    root.classList.toggle("dark", dark);
  }

  var btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", function () {
      var dark = !root.classList.contains("dark");
      apply(dark);
      try {
        localStorage.setItem("theme", dark ? "dark" : "light");
      } catch (e) {}
    });
  }

  // If the user hasn't picked explicitly, follow OS changes live.
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
      var stored;
      try {
        stored = localStorage.getItem("theme");
      } catch (err) {}
      if (stored !== "dark" && stored !== "light") apply(e.matches);
    });
  }
})();
