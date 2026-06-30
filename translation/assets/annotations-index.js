(function () {
  const list = document.getElementById("ann-list");
  if (!list) return;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  fetch("annotations-index.json")
    .then(function (r) {
      if (!r.ok) throw new Error("load index failed");
      return r.json();
    })
    .then(function (data) {
      render(data.pages || []);
    })
    .catch(function (e) {
      list.textContent = "加载批注索引失败：" + e.message;
    });

  function render(pages) {
    const html = pages.map(function (page) {
      const pairs = (page.pairs || []).map(function (p) {
        return [
          '<div class="ann-pair-row">',
          '  <span class="ann-pair-n">#' + p.n + "</span>",
          '  <span class="ann-pair-preview">' + escapeHtml(p.preview) + "</span>",
          '  <a class="ann-pair-link" href="' + page.page + "#pair-" + p.n + '">查看 →</a>',
          "</div>"
        ].join("");
      }).join("");
      const count = (page.pairs || []).length;
      return [
        '<section class="ann-chapter">',
        '  <div class="ann-chapter-head">',
        "    <span>" + escapeHtml(page.title) + "</span>",
        '    <span class="ann-chapter-count">' + count + " 段</span>",
        "  </div>",
        '  <div class="ann-chapter-body">' + pairs + "</div>",
        "</section>"
      ].join("");
    }).join("");
    list.innerHTML = html;
    attachToggles();
  }

  function attachToggles() {
    document.querySelectorAll(".ann-chapter-head").forEach(function (head) {
      head.addEventListener("click", function () {
        head.parentElement.classList.toggle("open");
      });
    });
  }
})();
