(function () {
  const dataUrl = "annotations.json";
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
      '    <h2 class="annotation-heading" id="annotation-modal-heading">批注</h2>',
      '    <button class="annotation-close" type="button">关闭</button>',
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
    const list = modal.querySelector(".annotation-list");
    list.innerHTML = items.map(function (item) {
      return [
        '<article class="annotation-card">',
        '  <h3 class="annotation-title">' + escapeHtml(item.title) + "</h3>",
        '  <div class="annotation-body">' + item.body + "</div>",
        "</article>"
      ].join("");
    }).join("");
    modal.classList.add("is-open");
    document.body.classList.add("annotation-lock");

    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([list]);
    }
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

  function attachAnnotations(items) {
    const grouped = groupByPair(items.filter(function (item) {
      return item.page === pageName;
    }));

    document.querySelectorAll(".pair").forEach(function (pair, index) {
      const annotations = grouped.get(index + 1);
      if (!annotations || annotations.length === 0) return;

      const button = document.createElement("button");
      button.className = "annotation-button";
      button.type = "button";
      button.textContent = annotations.length > 1 ? "批注 " + annotations.length : "批注";
      button.addEventListener("click", function () {
        openModal(annotations);
      });
      pair.appendChild(button);
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
