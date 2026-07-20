(function () {
  "use strict";
  // 全局竖向分隔条：拖动调整英/中两栏宽度，所有 .pair 同步缩放
  // 比例写入 localStorage 持久化；双击复位 50/50；窄屏 (<=760px) 不启用
  //
  // 性能要点（避免拖动卡顿）：
  // 1. mousedown 时缓存 pairLeft/pairWidth/mainLeft，mousemove 不再读 getBoundingClientRect
  // 2. mousemove 只更新 targetPct，requestAnimationFrame 每帧最多 apply 一次
  // 3. apply 期间 splitter.left 用算术算出，不读 DOM 布局
  // 4. 拖动期间 disconnect ResizeObserver，避免 重排→observer→读布局→再重排 循环
  // 5. will-change: left 提示浏览器把 splitter 提升为独立图层
  var STORAGE_KEY = "cv-col-split-pct";
  var MIN_PCT = 20, MAX_PCT = 80, DEFAULT_PCT = 50;

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  function getMain() { return document.querySelector("main.doc"); }

  function clampPct(p) {
    p = Number(p);
    if (!Number.isFinite(p)) return DEFAULT_PCT;
    return Math.min(MAX_PCT, Math.max(MIN_PCT, p));
  }

  function loadPct() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return v ? clampPct(v) : DEFAULT_PCT;
    } catch (e) { return DEFAULT_PCT; }
  }

  function savePct(p) {
    try { localStorage.setItem(STORAGE_KEY, String(p)); } catch (e) {}
  }

  var splitterEl = null;
  var currentPct = DEFAULT_PCT;
  var ro = null; // ResizeObserver

  function applyPct(pct) {
    currentPct = pct;
    var main = getMain();
    if (!main) return;
    main.style.setProperty("--col-en", pct + "fr");
    main.style.setProperty("--col-zh", (100 - pct) + "fr");
    main.style.setProperty("--col-en-pct", pct);
  }

  // 非拖动场景的精确定位：读 en.right 一次
  function positionSplitter() {
    var main = getMain();
    if (!main || !splitterEl) return;
    var en = main.querySelector(".pair > .en");
    if (!en) { splitterEl.style.display = "none"; return; }
    var mainRect = main.getBoundingClientRect();
    var enRect = en.getBoundingClientRect();
    splitterEl.style.left = (enRect.right - mainRect.left) + "px";
    splitterEl.style.display = "";
  }

  function ensureSplitter() {
    var main = getMain();
    if (!main) return;
    if (splitterEl && splitterEl.parentNode) return;
    if (getComputedStyle(main).position === "static") {
      main.style.position = "relative";
    }
    splitterEl = document.createElement("div");
    splitterEl.className = "cv-splitter";
    splitterEl.setAttribute("role", "separator");
    splitterEl.setAttribute("aria-orientation", "vertical");
    splitterEl.setAttribute("aria-label", "拖动调整英中两栏宽度，双击复位");
    splitterEl.title = "拖动调整宽度 · 双击复位";
    splitterEl.style.willChange = "left";
    main.insertBefore(splitterEl, main.firstChild);
    bindDrag(splitterEl);
  }

  function bindDrag(el) {
    var dragging = false;
    var cache = null; // {pairLeft, pairWidth, mainLeft}
    var rafId = 0;
    var targetPct = DEFAULT_PCT;

    function buildCache() {
      var main = getMain();
      if (!main) return null;
      var en = main.querySelector(".pair > .en");
      var zh = main.querySelector(".pair > .zh");
      if (!en || !zh) return null;
      var enR = en.getBoundingClientRect();
      var zhR = zh.getBoundingClientRect();
      var mainR = main.getBoundingClientRect();
      return { pairLeft: enR.left, pairWidth: enR.width + zhR.width, mainLeft: mainR.left };
    }

    function applyFromCache(pct) {
      applyPct(pct);
      // 拖动期间 splitter 直接跟鼠标，不读 DOM
      if (cache) {
        splitterEl.style.left = (cache.pairLeft + cache.pairWidth * pct / 100 - cache.mainLeft) + "px";
      }
    }

    function scheduleApply() {
      if (rafId) return;
      rafId = requestAnimationFrame(function () {
        rafId = 0;
        applyFromCache(targetPct);
      });
    }

    function startDrag() {
      dragging = true;
      el.classList.add("is-dragging");
      document.body.classList.add("cv-dragging");
      cache = buildCache();
      if (ro) ro.disconnect();
    }

    function endDrag() {
      if (!dragging) return;
      dragging = false;
      el.classList.remove("is-dragging");
      document.body.classList.remove("cv-dragging");
      if (rafId) { cancelAnimationFrame(rafId); rafId = 0; }
      applyFromCache(targetPct);
      savePct(currentPct);
      cache = null;
      if (ro) {
        var main = getMain();
        if (main) {
          ro.observe(main);
          var pair = main.querySelector(".pair");
          if (pair) ro.observe(pair);
        }
      }
      positionSplitter();
    }

    el.addEventListener("mousedown", function (e) {
      startDrag();
      e.preventDefault();
    });

    document.addEventListener("mousemove", function (e) {
      if (!dragging || !cache) return;
      targetPct = clampPct(((e.clientX - cache.pairLeft) / cache.pairWidth) * 100);
      scheduleApply();
    });

    document.addEventListener("mouseup", endDrag);

    el.addEventListener("dblclick", function () {
      targetPct = DEFAULT_PCT;
      applyPct(DEFAULT_PCT);
      positionSplitter();
      savePct(DEFAULT_PCT);
    });

    // 触摸
    el.addEventListener("touchstart", function (e) {
      if (e.touches.length !== 1) return;
      startDrag();
      e.preventDefault();
    }, { passive: false });

    document.addEventListener("touchmove", function (e) {
      if (!dragging || !cache || e.touches.length !== 1) return;
      var t = e.touches[0];
      targetPct = clampPct(((t.clientX - cache.pairLeft) / cache.pairWidth) * 100);
      scheduleApply();
      e.preventDefault();
    }, { passive: false });

    document.addEventListener("touchend", endDrag);
    document.addEventListener("touchcancel", endDrag);
  }

  function isMobile() {
    return window.matchMedia("(max-width: 760px)").matches;
  }

  function init() {
    if (isMobile()) return;
    var main = getMain();
    if (!main) return;
    if (!main.querySelector(".pair")) return;
    ensureSplitter();
    applyPct(loadPct());
    positionSplitter();

    if (window.ResizeObserver) {
      ro = new ResizeObserver(function () { positionSplitter(); });
      ro.observe(main);
      var pair = main.querySelector(".pair");
      if (pair) ro.observe(pair);
    } else {
      window.addEventListener("resize", positionSplitter);
    }
    window.addEventListener("load", positionSplitter);
    if (window.MathJax && window.MathJax.startup) {
      window.MathJax.startup.promise.then(positionSplitter).catch(function(){});
    }
  }

  ready(init);
})();
