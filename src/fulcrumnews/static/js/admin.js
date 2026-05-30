// "Verify feed" button — dry-runs the RSS URL via /admin/outlets/verify before saving.
(function () {
  var btn = document.getElementById("verify-btn");
  if (!btn) return;
  var input = document.getElementById("feed_url");
  var result = document.getElementById("verify-result");
  var endpoint = result.getAttribute("data-verify-url");
  var tokenEl = document.querySelector("input[name=token]");
  var token = tokenEl ? tokenEl.value : "";

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  btn.addEventListener("click", async function () {
    var url = (input.value || "").trim();
    if (!url) {
      result.innerHTML = '<span class="text-red-600">Enter a feed URL first.</span>';
      return;
    }
    var orig = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Checking…";
    result.innerHTML = '<span class="text-neutral-400">Checking feed…</span>';
    try {
      var body = new URLSearchParams({ feed_url: url, token: token });
      var resp = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });
      var data = await resp.json();
      if (data.ok) {
        var titles = (data.sample_titles || [])
          .map(function (t) { return "<li>" + esc(t) + "</li>"; })
          .join("");
        var bodyNote = data.body_extracted
          ? '<span class="text-green-700">✓ full text extracted</span>'
          : '<span class="text-amber-600">⚠ headlines only (weak body extraction)</span>';
        result.innerHTML =
          '<div class="rounded-lg bg-green-50 p-3 ring-1 ring-green-200">' +
          '<p class="font-medium text-green-800">✓ ' + esc(data.message) + "</p>" +
          '<p class="mt-1 text-xs text-neutral-600">' + bodyNote + "</p>" +
          (titles ? '<ul class="mt-2 list-disc pl-5 text-xs text-neutral-600">' + titles + "</ul>" : "") +
          "</div>";
      } else {
        result.innerHTML =
          '<div class="rounded-lg bg-red-50 p-3 ring-1 ring-red-200 text-red-700">✗ ' +
          esc(data.message) + "</div>";
      }
    } catch (e) {
      result.innerHTML = '<span class="text-red-600">Verification request failed.</span>';
    } finally {
      btn.disabled = false;
      btn.textContent = orig;
    }
  });
})();
