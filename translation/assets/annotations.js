(function () {
  const dataUrl = "annotations.json";
  const pageName = window.location.pathname.split("/").pop() || "index.html";
  const authoringMode = new URLSearchParams(window.location.search).get("annotate") === "1";

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

  function openModal(items) {
    const modal = ensureModal();
    modal.querySelector(".annotation-heading").textContent = "\u6279\u6ce8";
    const list = modal.querySelector(".annotation-list");
    list.innerHTML = items.map(function (item) {
      return [
        '<article class="annotation-card">',
        '  <h3 class="annotation-title">' + escapeHtml(item.title) + "</h3>",
        '  <div class="annotation-body">' + item.body + "</div>",
        "</article>"
      ].join("");
    }).join("");
    showModal(modal);

    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([list]);
    }
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

  function annotationObject(pairIndex, title, body) {
    return {
      page: pageName,
      pair: pairIndex,
      title: title,
      body: body
    };
  }

  function renderGeneratedJson(pairIndex, form) {
    const title = form.querySelector("[data-annotation-title]").value.trim();
    const body = form.querySelector("[data-annotation-body]").value.trim();
    const output = form.querySelector("[data-annotation-output]");
    output.value = JSON.stringify(annotationObject(pairIndex, title, body), null, 2);
    return output.value;
  }

  function downloadJson(value) {
    const blob = new Blob([value + "\n"], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "annotation-snippet.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  function openEditor(pairIndex) {
    const modal = ensureModal();
    modal.querySelector(".annotation-heading").textContent = "\u65b0\u589e\u6279\u6ce8";
    const list = modal.querySelector(".annotation-list");
    list.innerHTML = [
      '<form class="annotation-editor">',
      '  <div class="annotation-meta">page: <code>' + escapeHtml(pageName) + "</code> / pair: <code>" + pairIndex + "</code></div>",
      '  <label class="annotation-field">',
      '    <span>\u6807\u9898</span>',
      '    <input class="annotation-input" data-annotation-title type="text" value="">',
      "  </label>",
      '  <label class="annotation-field">',
      '    <span>\u6b63\u6587 HTML</span>',
      '    <textarea class="annotation-textarea" data-annotation-body rows="8" placeholder="<p>\u8fd9\u91cc\u5199\u6279\u6ce8\uff0c\u652f\u6301 MathJax\uff1a$x \\\\in C$\u3002</p>"></textarea>',
      "  </label>",
      '  <label class="annotation-field">',
      '    <span>\u751f\u6210\u7684 JSON</span>',
      '    <textarea class="annotation-output" data-annotation-output rows="9" readonly></textarea>',
      "  </label>",
      '  <div class="annotation-actions">',
      '    <button class="annotation-copy" type="button">\u590d\u5236 JSON</button>',
      '    <button class="annotation-download" type="button">\u4e0b\u8f7d JSON</button>',
      '    <span class="annotation-copy-status" aria-live="polite"></span>',
      "  </div>",
      "</form>"
    ].join("");

    const form = list.querySelector(".annotation-editor");
    const status = form.querySelector(".annotation-copy-status");
    form.addEventListener("input", function () {
      renderGeneratedJson(pairIndex, form);
      status.textContent = "";
    });
    form.querySelector(".annotation-copy").addEventListener("click", function () {
      const value = renderGeneratedJson(pairIndex, form);
      navigator.clipboard.writeText(value).then(function () {
        status.textContent = "\u5df2\u590d\u5236";
      });
    });
    form.querySelector(".annotation-download").addEventListener("click", function () {
      downloadJson(renderGeneratedJson(pairIndex, form));
    });
    renderGeneratedJson(pairIndex, form);
    showModal(modal);
    form.querySelector("[data-annotation-title]").focus();
  }

  function attachAuthoringButton(pair, pairIndex, hasExistingAnnotations) {
    const button = document.createElement("button");
    button.className = hasExistingAnnotations
      ? "annotation-button annotation-add-button"
      : "annotation-button annotation-add-button annotation-add-button-single";
    button.type = "button";
    button.textContent = "+\u6279\u6ce8";
    button.addEventListener("click", function () {
      openEditor(pairIndex);
    });
    pair.appendChild(button);
  }

  function attachAnnotations(items) {
    const grouped = groupByPair(items.filter(function (item) {
      return item.page === pageName;
    }));

    document.querySelectorAll(".pair").forEach(function (pair, index) {
      const pairIndex = index + 1;
      const annotations = grouped.get(pairIndex);

      if (annotations && annotations.length > 0) {
        const button = document.createElement("button");
        button.className = "annotation-button";
        button.type = "button";
        button.textContent = annotations.length > 1 ? "\u6279\u6ce8 " + annotations.length : "\u6279\u6ce8";
        button.addEventListener("click", function () {
          openModal(annotations);
        });
        pair.appendChild(button);
      }

      if (authoringMode) {
        attachAuthoringButton(pair, pairIndex, !!(annotations && annotations.length > 0));
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeModal();
  });

  fetch(dataUrl)
    .then(function (response) {
      if (!response.ok) throw new Error("Failed to load " + dataUrl);
      return response.json();
    })
    .then(attachAnnotations);
})();
