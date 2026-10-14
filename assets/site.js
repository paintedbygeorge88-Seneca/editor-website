// George Garnish portfolio: menu, galleries, lightbox and video embeds. No libraries.
(function () {
  "use strict";

  // ---------- Videos ----------
  function embedUrl(spec, autoplay) {
    var parts = spec.split(":"), provider = parts[0], id = parts[1];
    var ap = autoplay ? 1 : 0;
    if (provider === "vimeo") return "https://player.vimeo.com/video/" + id + "?autoplay=" + ap + "&dnt=1";
    return "https://www.youtube-nocookie.com/embed/" + id + "?rel=0&autoplay=" + ap;
  }
  function makeIframe(spec, autoplay) {
    var f = document.createElement("iframe");
    f.src = embedUrl(spec, autoplay);
    f.allow = "autoplay; fullscreen; picture-in-picture; encrypted-media";
    f.allowFullscreen = true;
    f.title = "Video player";
    return f;
  }
  document.querySelectorAll(".embed[data-embed]").forEach(function (el) {
    el.appendChild(makeIframe(el.dataset.embed, false));
  });

  // ---------- Menu ----------
  document.querySelectorAll(".side .folder > button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var li = btn.parentElement, opening = !li.classList.contains("open");
      document.querySelectorAll(".side .folder.open").forEach(function (o) {
        o.classList.remove("open");
        o.querySelector("button").setAttribute("aria-expanded", "false");
      });
      if (opening) { li.classList.add("open"); btn.setAttribute("aria-expanded", "true"); }
    });
  });
  var toggle = document.querySelector(".menu-toggle"), nav = document.getElementById("site-nav");
  if (toggle) toggle.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  // Same rule Squarespace used (checked against the live site): width ÷ column width, rounded down.
  function columnsFor(el) {
    if (window.innerWidth < 768) return 1;
    var colw = parseFloat(getComputedStyle(el).getPropertyValue("--colw")) || 300;
    return Math.max(1, Math.floor(el.clientWidth / colw));
  }
  var grids = document.querySelectorAll(".autogrid");
  function layoutGrids() { grids.forEach(function (g) { g.style.setProperty("--n", columnsFor(g)); }); }
  layoutGrids();
  window.addEventListener("resize", layoutGrids);

  // ---------- Masonry: deal cards into the shortest column ----------
  function layoutMasonry(m) {
    var cards = m._cards || (m._cards = Array.prototype.slice.call(m.querySelectorAll(":scope > .card")));
    var want = columnsFor(m);
    if (m._n === want) return;
    m._n = want;
    m.innerHTML = "";
    var cols = [], heights = [];
    for (var i = 0; i < want; i++) {
      var c = document.createElement("div"); c.className = "mcol"; m.appendChild(c); cols.push(c); heights.push(0);
    }
    cards.forEach(function (card) {
      var img = card.querySelector("img");
      var ratio = img && img.width && img.height ? img.height / img.width : 1;
      var k = heights.indexOf(Math.min.apply(null, heights));
      cols[k].appendChild(card);
      heights[k] += ratio + (card.querySelector(".title") ? 0.08 : 0) + 0.04;
    });
  }
  var masonries = document.querySelectorAll(".masonry");
  masonries.forEach(layoutMasonry);
  window.addEventListener("resize", function () { masonries.forEach(layoutMasonry); });

  // ---------- Slider strips ----------
  document.querySelectorAll(".slider").forEach(function (s) {
    var strip = s.querySelector(".strip");
    var tiles = strip.querySelectorAll(".tile");
    function current() {
      var mid = strip.scrollLeft + strip.clientWidth / 2, best = 0, bestD = Infinity;
      tiles.forEach(function (t, i) {
        var d = Math.abs(t.offsetLeft + t.offsetWidth / 2 - mid);
        if (d < bestD) { bestD = d; best = i; }
      });
      return best;
    }
    function go(i) {
      var n = tiles.length; i = (i + n) % n;
      var t = tiles[i];
      strip.scrollTo({ left: t.offsetLeft + t.offsetWidth / 2 - strip.clientWidth / 2 });
    }
    s.querySelector(".prev").addEventListener("click", function () { go(current() - 1); });
    s.querySelector(".next").addEventListener("click", function () { go(current() + 1); });
    autoplay(s, function () { go(current() + 1); });
  });

  // ---------- Slideshows ----------
  document.querySelectorAll(".slideshow").forEach(function (s) {
    var slides = s.querySelectorAll(".slide"), thumbs = s.querySelectorAll(".thumb"), at = 0;
    function show(i) {
      at = (i + slides.length) % slides.length;
      slides.forEach(function (el, k) { el.classList.toggle("on", k === at); });
      thumbs.forEach(function (el, k) { el.classList.toggle("on", k === at); });
      var th = thumbs[at];
      if (th) th.parentElement.scrollTo({ left: th.offsetLeft - th.parentElement.clientWidth / 2 + th.offsetWidth / 2, behavior: "smooth" });
    }
    s.querySelector(".prev").addEventListener("click", function () { show(at - 1); });
    s.querySelector(".next").addEventListener("click", function () { show(at + 1); });
    thumbs.forEach(function (t, k) { t.addEventListener("click", function () { show(k); }); });
    autoplay(s, function () { show(at + 1); });
  });

  // Autoplay that pauses while hovered, while off-screen, and for people who prefer less motion.
  function autoplay(el, step) {
    var secs = parseFloat(el.dataset.autoplay);
    if (!secs || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var visible = false, hover = false;
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(el);
    } else { visible = true; }
    el.addEventListener("mouseenter", function () { hover = true; });
    el.addEventListener("mouseleave", function () { hover = false; });
    setInterval(function () { if (visible && !hover && !document.hidden) step(); }, secs * 1000);
  }

  // ---------- Lightbox ----------
  var lb = document.createElement("div");
  lb.className = "lightbox";
  lb.setAttribute("role", "dialog");
  lb.setAttribute("aria-modal", "true");
  lb.innerHTML = '<div class="lb-content"></div>' +
    '<button type="button" class="lb-close" aria-label="Close">&times;</button>' +
    '<button type="button" class="arrow prev" aria-label="Previous"></button>' +
    '<button type="button" class="arrow next" aria-label="Next"></button>';
  document.body.appendChild(lb);
  var box = lb.querySelector(".lb-content"), group = [], index = 0, opener = null;

  function render() {
    var t = group[index];
    box.innerHTML = "";
    if (t.dataset.video) {
      var wrap = document.createElement("div"); wrap.className = "embed";
      wrap.appendChild(makeIframe(t.dataset.video, true));
      box.appendChild(wrap);
    } else {
      var img = document.createElement("img");
      var src = t.querySelector("img");
      img.src = t.dataset.full; img.alt = src ? src.alt : "";
      box.appendChild(img);
    }
    var many = group.length > 1;
    lb.querySelector(".prev").hidden = !many;
    lb.querySelector(".next").hidden = !many;
  }
  function open(tile) {
    var g = tile.closest(".lb-group");
    group = g ? Array.prototype.slice.call(g.querySelectorAll("[data-full]")) : [tile];
    index = Math.max(0, group.indexOf(tile));
    opener = tile;
    render();
    lb.classList.add("open");
    document.body.classList.add("lb-lock");
    lb.querySelector(".lb-close").focus();
  }
  function close() {
    lb.classList.remove("open");
    document.body.classList.remove("lb-lock");
    box.innerHTML = ""; // stops any playing video
    if (opener) opener.focus();
  }
  function step(d) { index = (index + d + group.length) % group.length; render(); }

  document.addEventListener("click", function (e) {
    var tile = e.target.closest("[data-full]");
    if (tile && !lb.contains(tile)) { e.preventDefault(); open(tile); }
  });
  lb.querySelector(".lb-close").addEventListener("click", close);
  lb.querySelector(".prev").addEventListener("click", function () { step(-1); });
  lb.querySelector(".next").addEventListener("click", function () { step(1); });
  lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft" && group.length > 1) step(-1);
    else if (e.key === "ArrowRight" && group.length > 1) step(1);
  });
})();
