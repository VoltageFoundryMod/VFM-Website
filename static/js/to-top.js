/* Floating "back to top" button — fades in once the page is scrolled. */
(function () {
  var btn = document.querySelector(".to-top");
  if (!btn) return;

  var SHOW_AFTER = 600; // px scrolled
  var ticking = false;

  function update() {
    ticking = false;
    btn.classList.toggle("is-visible", window.scrollY > SHOW_AFTER);
  }

  window.addEventListener(
    "scroll",
    function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    },
    { passive: true },
  );

  btn.addEventListener("click", function () {
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
    // Scrolling away from a hash leaves it in the URL; drop it so a reload
    // doesn't jump straight back down.
    if (location.hash) {
      history.replaceState(null, "", location.pathname + location.search);
    }
  });

  update();
})();
