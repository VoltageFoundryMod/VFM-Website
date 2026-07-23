(function () {
  var root = document.getElementById("get");
  if (!root) return;
  var track = root.querySelector(".get-track");
  var slides = root.querySelectorAll(".get-slide");
  var tabs = root.querySelectorAll(".get-tab");
  var dots = root.querySelectorAll(".get-dot");
  var count = slides.length;
  var index = 0;
  var timer = null;
  var DELAY = 10000;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
    }, DELAY);
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
})();
