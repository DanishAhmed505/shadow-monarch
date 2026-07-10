(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Reading progress bar (article pages) ----
  (function () {
    var bar = document.getElementById("progress");
    if (!bar || !document.querySelector(".article")) return;
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    }
    document.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  })();

  // ---- Scroll reveal ----
  (function () {
    var els = document.querySelectorAll(".card, .pf-section, .stat");
    if (!els.length) return;
    if (reduce || !("IntersectionObserver" in window)) {
      els.forEach(function (e) { e.classList.add("revealed"); });
      return;
    }
    els.forEach(function (e) { e.classList.add("reveal"); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("revealed"); io.unobserve(en.target); }
      });
    }, { threshold: 0.08 });
    els.forEach(function (e) { io.observe(e); });
  })();

  // ---- Copy buttons on code blocks ----
  (function () {
    var pres = document.querySelectorAll(".prose pre");
    pres.forEach(function (pre) {
      var btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.type = "button";
      btn.textContent = "copy";
      btn.addEventListener("click", function () {
        var code = pre.querySelector("code") || pre;
        var text = code.innerText;
        function ok() { btn.textContent = "copied"; setTimeout(function () { btn.textContent = "copy"; }, 1500); }
        function fallback() {
          var ta = document.createElement("textarea");
          ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
          document.body.appendChild(ta); ta.select();
          try { document.execCommand("copy"); ok(); } catch (e) {}
          document.body.removeChild(ta);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(ok, fallback);
        } else { fallback(); }
      });
      pre.appendChild(btn);
    });
  })();

  // ---- Animated stat counters (portfolio) ----
  (function () {
    var nums = document.querySelectorAll(".stat-num");
    if (!nums.length || reduce || !("IntersectionObserver" in window)) return;
    function animate(el) {
      var m = el.textContent.match(/^(\d+)(\D*)$/);
      if (!m) return; // leave "#1", "NASA", "Top 5%", "Finalist" alone
      var target = parseInt(m[1], 10), suffix = m[2], start = null, dur = 900;
      function step(t) {
        if (!start) start = t;
        var p = Math.min((t - start) / dur, 1);
        el.textContent = Math.floor(p * target) + suffix;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { animate(en.target.querySelector ? en.target : en.target); io.unobserve(en.target); }
      });
    }, { threshold: 0.6 });
    nums.forEach(function (n) { io.observe(n); });
  })();

  // ---- Claps + reactions (real, shared counts via a Cloudflare Worker) ----
  (function () {
    var box = document.querySelector(".reactions");
    if (!box) return;
    var slug = box.getAttribute("data-slug") || location.pathname;
    var API = "https://shadow-monarch-reactions.danishahmed2004505.workers.dev/reactions";

    // localStorage here only remembers what THIS browser has already done,
    // so it can't double-count itself; the numbers shown come from the API.
    var LKEY = "reacted:" + slug;
    var local = {};
    try { local = JSON.parse(localStorage.getItem(LKEY) || "{}"); } catch (e) {}
    function saveLocal() { try { localStorage.setItem(LKEY, JSON.stringify(local)); } catch (e) {} }

    function floatPlus(btn) {
      var s = document.createElement("span");
      s.className = "clap-plus"; s.textContent = "+1";
      btn.appendChild(s);
      setTimeout(function () { if (s.parentNode) s.parentNode.removeChild(s); }, 700);
    }
    function pop(el) { el.classList.remove("pop"); void el.offsetWidth; el.classList.add("pop"); }

    var clapBtn = box.querySelector(".clap-btn");
    var clapCount = box.querySelector(".clap-count");
    var MAX_LOCAL_CLAPS = 50;
    local.clap = local.clap || 0;
    if (local.clap > 0) clapBtn.classList.add("clapped");

    var reactBtns = {};
    box.querySelectorAll(".react-btn").forEach(function (btn) {
      var key = btn.getAttribute("data-key");
      reactBtns[key] = btn;
      if (local[key]) btn.classList.add("active");
    });

    function render(counts) {
      clapCount.textContent = counts.clap || 0;
      Object.keys(reactBtns).forEach(function (key) {
        var n = counts[key] || 0;
        var el = reactBtns[key].querySelector(".react-count");
        if (el) el.textContent = n > 0 ? n : "";
      });
    }

    function api(method, type) {
      var url = API + "?slug=" + encodeURIComponent(slug) + (type ? "&type=" + type : "");
      return fetch(url, { method: method }).then(function (r) { return r.json(); });
    }

    api("GET").then(render).catch(function () {});

    clapBtn.addEventListener("click", function () {
      if (local.clap >= MAX_LOCAL_CLAPS) return;
      local.clap++;
      clapBtn.classList.add("clapped");
      pop(clapBtn.querySelector(".clap-emoji"));
      floatPlus(clapBtn);
      saveLocal();
      api("POST", "clap").then(render).catch(function () {});
    });

    Object.keys(reactBtns).forEach(function (key) {
      var btn = reactBtns[key];
      btn.addEventListener("click", function () {
        if (local[key]) return; // one reaction of each kind per browser
        local[key] = 1;
        btn.classList.add("active");
        pop(btn);
        saveLocal();
        api("POST", key).then(render).catch(function () {});
      });
    });
  })();

  // ---- Typewriter (hero) ----
  (function () {
    var el = document.getElementById("typed");
    if (!el) return;
    var phrases = (el.getAttribute("data-phrases") || "").split("|").filter(Boolean);
    if (!phrases.length) return;
    if (reduce) { el.textContent = phrases[0]; return; }
    var pi = 0, ci = 0, deleting = false;
    function tick() {
      var word = phrases[pi];
      ci += deleting ? -1 : 1;
      el.textContent = word.slice(0, ci);
      var delay = deleting ? 45 : 95;
      if (!deleting && ci === word.length) { deleting = true; delay = 1500; }
      else if (deleting && ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; delay = 350; }
      setTimeout(tick, delay);
    }
    tick();
  })();

  // ---- Circuit network (full-page background: green nodes + connecting lines) ----
  (function () {
    var canvas = document.getElementById("bg-net");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    var DPR = Math.min(window.devicePixelRatio || 1, 2);
    var W, H, nodes = [], count, maxDist;

    function init() {
      W = canvas.offsetWidth; H = canvas.offsetHeight;
      canvas.width = W * DPR; canvas.height = H * DPR;
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      count = Math.max(20, Math.min(52, Math.round((W * H) / 42000)));
      maxDist = Math.min(200, W / 6);
      nodes = [];
      for (var i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * W, y: Math.random() * H,
          vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3
        });
      }
    }

    function frame() {
      ctx.clearRect(0, 0, W, H);
      var i, a, b;
      for (i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;
      }
      ctx.lineWidth = 1;
      for (a = 0; a < nodes.length; a++) {
        for (b = a + 1; b < nodes.length; b++) {
          var dx = nodes[a].x - nodes[b].x, dy = nodes[a].y - nodes[b].y;
          var d = Math.sqrt(dx * dx + dy * dy);
          if (d < maxDist) {
            ctx.strokeStyle = "rgba(159,239,0," + ((1 - d / maxDist) * 0.5).toFixed(3) + ")";
            ctx.beginPath();
            ctx.moveTo(nodes[a].x, nodes[a].y);
            ctx.lineTo(nodes[b].x, nodes[b].y);
            ctx.stroke();
          }
        }
      }
      ctx.fillStyle = "rgba(159,239,0,0.85)";
      for (i = 0; i < nodes.length; i++) {
        ctx.beginPath();
        ctx.arc(nodes[i].x, nodes[i].y, 1.7, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    init();
    window.addEventListener("resize", init);
    if (reduce) { frame(); return; }        // static network for reduced-motion
    var timer = setInterval(frame, 33);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { clearInterval(timer); timer = null; }
      else if (!timer) { timer = setInterval(frame, 33); }
    });
  })();
})();
