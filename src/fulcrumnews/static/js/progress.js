// Polls /api/progress and renders the global + per-phase progress bars during a refresh.
(function () {
  var panel = document.getElementById("pipeline-progress");
  if (!panel) return;
  var statusEl = document.getElementById("pp-status");
  var globalEl = document.getElementById("pp-global");
  var globalBar = document.getElementById("pp-global-bar");
  var tasksEl = document.getElementById("pp-tasks");
  var BAR_COLORS = { cluster: "bg-sky-500", summarize: "bg-brand-600", format: "bg-emerald-500" };
  var ORDER = ["cluster", "summarize", "format"];
  var wasRunning = false;

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function renderTasks(tasks) {
    tasksEl.innerHTML = ORDER.map(function (key) {
      var t = tasks[key] || { label: key, done: 0, total: 0, percent: 0, current: "" };
      var color = BAR_COLORS[key] || "bg-brand-600";
      return (
        '<div>' +
        '<div class="flex items-center justify-between text-[11px] font-medium">' +
        '<span>' + esc(t.label) + '</span>' +
        '<span class="text-neutral-500 dark:text-neutral-400">' + t.done + '/' + t.total + '</span>' +
        '</div>' +
        '<div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-700">' +
        '<div class="h-full ' + color + ' transition-all duration-500" style="width:' + (t.percent || 0) + '%"></div>' +
        '</div>' +
        '<div class="mt-1 truncate text-[10px] text-neutral-400 dark:text-neutral-500">' + esc(t.current || "") + '</div>' +
        '</div>'
      );
    }).join("");
  }

  async function poll() {
    var data;
    try {
      var r = await fetch("/api/progress", { cache: "no-store" });
      data = await r.json();
    } catch (e) {
      return;
    }

    if (data.running) {
      panel.classList.remove("hidden");
      statusEl.textContent = data.status || "Refreshing feeds…";
      globalEl.textContent = (data.global_percent || 0) + "%";
      globalBar.style.width = (data.global_percent || 0) + "%";
      renderTasks(data.tasks || {});
      wasRunning = true;
    } else if (wasRunning) {
      // Just finished — show new stories.
      wasRunning = false;
      window.location.reload();
    } else {
      panel.classList.add("hidden");
    }
  }

  poll();
  setInterval(poll, 1200);
})();
