(function () {
  const annotationsUrl = "annotations.json";
  const giscusConfigUrl = "giscus-config.json";
  const annotatedPairsUrl = "annotated-pairs.json";
  const pageName = window.location.pathname.split("/").pop() || "index.html";

  function ensureModal() {
    let modal = document.querySelector(".annotation-modal");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "annotation-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-labelledby", "annotation-modal-heading");
    modal.innerHTML = [
      '<div class="annotation-panel">',
      '  <div class="annotation-header">',
      '    <h2 class="annotation-heading" id="annotation-modal-heading"></h2>',
      '    <button class="annotation-close" type="button">\u5173\u95ed</button>',
      "  </div>",
      '  <div class="annotation-list"></div>',
      "</div>"
    ].join("");

    modal.addEventListener("click", function (event) {
      if (event.target === modal) closeModal();
    });
    modal.querySelector(".annotation-close").addEventListener("click", closeModal);
    document.body.appendChild(modal);
    return modal;
  }

  function closeModal() {
    const modal = document.querySelector(".annotation-modal");
    if (!modal) return;
    modal.classList.remove("is-open");
    document.body.classList.remove("annotation-lock");
  }

  function showModal(modal) {
    modal.classList.add("is-open");
    document.body.classList.add("annotation-lock");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function groupByPair(items) {
    return items.reduce(function (groups, item) {
      const pair = Number(item.pair);
      if (!Number.isInteger(pair) || pair < 1) return groups;
      if (!groups.has(pair)) groups.set(pair, []);
      groups.get(pair).push(item);
      return groups;
    }, new Map());
  }

  function staticAnnotationHtml(items) {
    if (!items || items.length === 0) return "";

    return [
      '<section class="annotation-section">',
      '  <h3 class="annotation-section-title">\u7ad9\u5185\u6279\u6ce8</h3>',
      items.map(function (item) {
        return [
          '<article class="annotation-card">',
          '  <h4 class="annotation-title">' + escapeHtml(item.title) + "</h4>",
          '  <div class="annotation-body">' + item.body + "</div>",
          "</article>"
        ].join("");
      }).join(""),
      "</section>"
    ].join("");
  }

  function requiredConfigMissing(config) {
    return ["repo", "repoId", "category", "categoryId"].filter(function (key) {
      return !config[key] || !String(config[key]).trim();
    });
  }

  function setupHtml(term, missing) {
    return [
      '<section class="annotation-setup">',
      '  <h3 class="annotation-section-title">Giscus \u672a\u914d\u7f6e</h3>',
      "  <p>\u8981\u5728 GitHub Pages \u4e0a\u76f4\u63a5\u65b0\u589e\u6279\u6ce8\uff0c\u9700\u8981\u5148\u5728 <a href=\"https://giscus.app\" target=\"_blank\" rel=\"noopener\">giscus.app</a> \u751f\u6210\u771f\u5b9e\u914d\u7f6e\u3002</p>",
      "  <p>\u5f53\u524d\u7f3a\u5c11\uff1a<code>" + missing.map(escapeHtml).join("</code>, <code>") + "</code></p>",
      '  <p class="annotation-term">\u672c\u6bb5 term: <code>' + escapeHtml(term) + "</code></p>",
      "</section>"
    ].join("");
  }

  function giscusContainerHtml(term) {
    return [
      '<section class="annotation-section">',
      '  <h3 class="annotation-section-title">GitHub \u8ba8\u8bba</h3>',
      '  <p class="annotation-term">term: <code>' + escapeHtml(term) + "</code></p>",
      '  <div class="annotation-giscus"></div>',
      "</section>"
    ].join("");
  }

  function loadGiscus(container, config, term) {
    const script = document.createElement("script");
    script.src = "https://giscus.app/client.js";
    script.async = true;
    script.crossOrigin = "anonymous";
    script.setAttribute("data-repo", config.repo);
    script.setAttribute("data-repo-id", config.repoId);
    script.setAttribute("data-category", config.category);
    script.setAttribute("data-category-id", config.categoryId);
    script.setAttribute("data-mapping", "specific");
    script.setAttribute("data-term", term);
    script.setAttribute("data-strict", "1");
    script.setAttribute("data-reactions-enabled", config.reactionsEnabled || "1");
    script.setAttribute("data-emit-metadata", config.emitMetadata || "0");
    script.setAttribute("data-input-position", config.inputPosition || "bottom");
    script.setAttribute("data-theme", config.theme || "light");
    script.setAttribute("data-lang", config.lang || "zh-CN");
    container.appendChild(script);
  }

  function openPairModal(pairIndex, items, config) {
    const modal = ensureModal();
    const term = pageName + "#pair-" + pairIndex;
    const missing = requiredConfigMissing(config);
    modal.querySelector(".annotation-heading").textContent = "\u6279\u6ce8";

    const list = modal.querySelector(".annotation-list");
    list.innerHTML = [
      '<div class="annotation-meta">page: <code>' + escapeHtml(pageName) + "</code> / pair: <code>" + pairIndex + "</code></div>",
      staticAnnotationHtml(items),
      missing.length ? setupHtml(term, missing) : giscusContainerHtml(term)
    ].join("");

    showModal(modal);

    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([list]);
    }

    if (missing.length === 0) {
      loadGiscus(list.querySelector(".annotation-giscus"), config, term);
    }
  }

  function attachAnnotations(items, config, annotatedSet) {
    const grouped = groupByPair(items.filter(function (item) {
      return item.page === pageName;
    }));

    document.querySelectorAll(".pair").forEach(function (pair, index) {
      const pairIndex = index + 1;
      const annotations = grouped.get(pairIndex) || [];
      const giscusCount = annotatedSet ? annotatedSet.get(pairIndex) : 0;
      const button = document.createElement("button");
      button.className = "annotation-button";
      button.type = "button";
      if (giscusCount > 0) {
        button.classList.add("has-comments");
        button.textContent = "💬 " + giscusCount;
        pair.classList.add("has-annotations");
      } else if (annotations.length > 0) {
        button.textContent = "\u6279\u6ce8 " + annotations.length;
      } else {
        button.textContent = "\u6279\u6ce8";
      }
      button.addEventListener("click", function () {
        openPairModal(pairIndex, annotations, config);
      });
      pair.appendChild(button);
    });
  }

  function fetchJson(url) {
    return fetch(url).then(function (response) {
      if (!response.ok) throw new Error("Failed to load " + url);
      return response.json();
    });
  }

  function openPairFromHash() {
    const m = /^#pair-(\d+)$/.exec(window.location.hash);
    if (!m) return;
    const n = Number(m[1]);
    const pairs = document.querySelectorAll(".pair");
    if (n < 1 || n > pairs.length) return;
    const btn = pairs[n - 1].querySelector(".annotation-button");
    if (btn) btn.click();
  }

  function buildAnnotatedSet(data) {
    const set = new Map();
    if (!data || !data.pairs) return set;
    data.pairs.forEach(function (p) {
      if (p.page === pageName && p.pair > 0) {
        set.set(p.pair, p.comments || 0);
      }
    });
    return set;
  }

  function fetchJsonSafe(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) return null;
      return r.json();
    }).catch(function () { return null; });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeModal();
  });

  Promise.all([
    fetchJson(annotationsUrl),
    fetchJson(giscusConfigUrl),
    fetchJsonSafe(annotatedPairsUrl)
  ]).then(function (results) {
    attachAnnotations(results[0], results[1], buildAnnotatedSet(results[2]));
    openPairFromHash();
  });
})();
