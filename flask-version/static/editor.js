(function () {
  var textarea = document.getElementById("content");
  var preview = document.getElementById("preview");
  if (!textarea || !preview) return;

  var timer = null;
  var lastSent = null;

  function renderPreview() {
    var text = textarea.value;
    if (text === lastSent) return;
    lastSent = text;

    var body = new URLSearchParams();
    body.set("content", text);
    body.set("csrf", window.CSRF_TOKEN);

    fetch(window.PREVIEW_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRF-Token": window.CSRF_TOKEN,
      },
      body: body.toString(),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        preview.innerHTML = data.html || "<p class='muted'>Nothing to preview yet.</p>";
      })
      .catch(function () {
        preview.innerHTML = "<p class='muted'>Preview unavailable.</p>";
      });
  }

  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(renderPreview, 350);
  }

  textarea.addEventListener("input", schedule);

  // Tab key inserts two spaces instead of leaving the textarea.
  textarea.addEventListener("keydown", function (e) {
    if (e.key === "Tab") {
      e.preventDefault();
      var start = this.selectionStart;
      var end = this.selectionEnd;
      this.value = this.value.substring(0, start) + "  " + this.value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
      schedule();
    }
  });

  // Warn before leaving with unsaved edits.
  var initial = textarea.value;
  var dirty = false;
  textarea.addEventListener("input", function () { dirty = true; });
  document.getElementById("editor-form").addEventListener("submit", function () {
    dirty = false;
  });
  window.addEventListener("beforeunload", function (e) {
    if (dirty && textarea.value !== initial) {
      e.preventDefault();
      e.returnValue = "";
    }
  });

  renderPreview();
})();
