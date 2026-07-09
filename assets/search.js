(function () {
  var dataEl = document.getElementById("search-index");
  var input = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  var feed = document.getElementById("post-feed");
  var featured = document.getElementById("featured-post");
  var filters = document.getElementById("filters");
  if (!dataEl || !input || !results || !feed) return;

  var posts = [];
  try { posts = JSON.parse(dataEl.textContent || "[]"); } catch (e) { posts = []; }

  // precompute a lowercase haystack per post
  posts.forEach(function (p) {
    p._hay = (p.title + " " + (p.subtitle || "") + " " +
      (p.tags || []).join(" ") + " " + (p.text || "")).toLowerCase();
  });

  var activeTerms = [];   // from the selected vulnerability chip ([] = all)

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function snippet(text, q) {
    if (!q) return "";
    var i = text.toLowerCase().indexOf(q);
    if (i < 0) return "";
    var start = Math.max(0, i - 45);
    var end = Math.min(text.length, i + q.length + 75);
    var s = (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
    var re = new RegExp("(" + escapeRe(q) + ")", "ig");
    return escapeHtml(s).replace(re, "<mark>$1</mark>");
  }

  // whole-token match (avoids "rce" matching inside "e-commerce"); no lookbehind
  // so it works in every browser
  function termMatch(hay, term) {
    return new RegExp("(?:^|[^a-z0-9])" + escapeRe(term) + "(?:[^a-z0-9]|$)").test(hay);
  }

  function matchesTerms(p) {
    if (!activeTerms.length) return true;
    for (var i = 0; i < activeTerms.length; i++) {
      if (termMatch(p._hay, activeTerms[i])) return true;
    }
    return false;
  }

  function render(matches, q) {
    if (!matches.length) {
      results.innerHTML = '<div class="search-empty">No writeups match your filter yet.</div>';
      return;
    }
    var html = '<div class="search-count">' + matches.length +
      ' writeup' + (matches.length > 1 ? "s" : "") + '</div>';
    matches.forEach(function (p) {
      var snip = snippet(p.text || "", q) || escapeHtml(p.subtitle || "");
      var tags = (p.tags || []).map(function (t) {
        return '<span class="tag">' + escapeHtml(t) + "</span>";
      }).join(" ");
      html += '<a class="search-hit" href="' + encodeURI(p.url) + '">' +
        '<div class="search-hit-title">' + escapeHtml(p.title) + "</div>" +
        (snip ? '<div class="search-hit-snip">' + snip + "</div>" : "") +
        '<div class="search-hit-meta">' + escapeHtml(p.date) +
        " · " + escapeHtml(String(p.reading_time)) + " min read " + tags + "</div>" +
        "</a>";
    });
    results.innerHTML = html;
  }

  function apply() {
    var q = input.value.trim().toLowerCase();

    // nothing active: show the normal feed
    if (!q && !activeTerms.length) {
      results.hidden = true;
      results.innerHTML = "";
      feed.hidden = false;
      if (featured) featured.hidden = false;
      return;
    }

    feed.hidden = true;
    if (featured) featured.hidden = true;
    results.hidden = false;

    var matches = posts.filter(function (p) {
      if (!matchesTerms(p)) return false;
      if (q && p._hay.indexOf(q) < 0) return false;
      return true;
    });

    // rank exact title hits first when text searching
    if (q) {
      matches.sort(function (a, b) {
        return (a.title.toLowerCase().indexOf(q) < 0) - (b.title.toLowerCase().indexOf(q) < 0);
      });
    }
    render(matches, q);
  }

  input.addEventListener("input", apply);

  if (filters) {
    filters.addEventListener("click", function (e) {
      var chip = e.target.closest(".filter-chip");
      if (!chip) return;
      var chips = filters.querySelectorAll(".filter-chip");
      for (var i = 0; i < chips.length; i++) chips[i].classList.remove("is-active");
      chip.classList.add("is-active");
      var terms = chip.getAttribute("data-terms") || "";
      activeTerms = terms ? terms.split("|").filter(Boolean) : [];
      apply();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
    } else if (e.key === "Escape" && document.activeElement === input) {
      input.value = "";
      apply();
      input.blur();
    }
  });
})();
