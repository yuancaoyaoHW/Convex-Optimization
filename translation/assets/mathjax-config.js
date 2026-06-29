// MathJax 3 configuration for bilingual convex optimization translation.
// Loaded before tex-svg.js so config is honored.
window.MathJax = {
  tex: {
    inlineMath: [
      ['$', '$'],
      ['\\(', '\\)']
    ],
    displayMath: [
      ['$$', '$$'],
      ['\\[', '\\]']
    ],
    processEscapes: true,
    tags: 'none',
    // ams environments: aligned, cases, matrix, etc.
    packages: { '[+]': ['ams', 'configmacros', 'newcommand'] }
  },
  options: {
    // render both columns
    skipHtmlTags: { '[-]': ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
  },
  svg: { fontCache: 'global' },
  startup: {
    ready: () => {
      MathJax.startup.defaultReady();
      // re-render after any dynamic content load
      MathJax.startup.promise.then(() => {
        document.dispatchEvent(new Event('mathjax-rendered'));
      });
    }
  }
};
