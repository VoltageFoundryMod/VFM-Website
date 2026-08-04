/* Tabbed carousel. Every [data-rotate] element on the page gets its own
   independent rotation: the VCV ↔ Hardware switcher and the workbench tools.
   Markup contract — .slider-tab / .slider-dot (both with data-slide="<n>"),
   .slider-track and .slider-slide. Set data-rotate="<ms>" to override the
   dwell time; auto-rotation is off under prefers-reduced-motion. */
(function () {
  var DEFAULT_DELAY = 10000;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-rotate]").forEach(function (root) {
    var track = root.querySelector(".slider-track");
    var slides = root.querySelectorAll(".slider-slide");
    var tabs = root.querySelectorAll(".slider-tab");
    var dots = root.querySelectorAll(".slider-dot");
    var count = slides.length;
    if (!track || count < 2) return; // nothing to rotate

    var delay = parseInt(root.dataset.rotate, 10) || DEFAULT_DELAY;
    var index = 0;
    var timer = null;

    function go(i) {
      index = (i + count) % count;
      track.style.transform = "translateX(" + index * -100 + "%)";
      tabs.forEach(function (t, n) {
        var on = n === index;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", on ? "true" : "false");
      });
      dots.forEach(function (d, n) {
        d.classList.toggle("is-active", n === index);
      });
      slides.forEach(function (s, n) {
        var off = n !== index; // keep offscreen panes laid out, but inert
        s.inert = off;
        s.setAttribute("aria-hidden", off ? "true" : "false");
      });
    }

    function start() {
      if (reduce || timer) return;
      timer = setInterval(function () {
        go(index + 1);
      }, delay);
    }
    function stop() {
      clearInterval(timer);
      timer = null;
    }
    function jump(i) {
      go(i);
      stop();
      start();
    } // reset the clock on interaction

    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        jump(+t.dataset.slide);
      });
    });
    dots.forEach(function (d) {
      d.addEventListener("click", function () {
        jump(+d.dataset.slide);
      });
    });
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);

    go(0);
    start();
  });
})();
