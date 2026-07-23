/* ── Panel magnifier ─────────────────────────────────────────────────────────
   Hovering a module panel opens a large zoom pane floating over the page,
   showing the slice of the panel under the cursor — silkscreen and jack labels
   stay readable without leaving the page. A marker drawn on the panel itself
   shows which slice is on screen. Pointer-based only: coarse pointers (touch)
   get the plain image.
--------------------------------------------------------------------------- */
(function () {
  // Panels render small (max-height 300px) but ship at a few times that, so the
  // pane magnifies up to the image's own resolution — past that it only blurs.
  var ZOOM_MIN = 2;
  var ZOOM_MAX = 4.5;
  var PANE_W = 460; // pane size, trimmed to fit the viewport
  var PANE_H_VH = 0.82;
  var GAP = 20; // space between panel and pane

  function fine() {
    return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  }

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function attach(box) {
    var img = box.querySelector("img");
    if (!img) return;

    var marker = document.createElement("div");
    marker.className = "panel-zoom-marker";
    box.appendChild(marker);

    var pane = document.createElement("div");
    pane.className = "panel-zoom-pane";
    pane.style.backgroundImage = 'url("' + (img.currentSrc || img.src) + '")';
    document.body.appendChild(pane);

    var rect = null; // image box, viewport coords
    var zoom = ZOOM_MIN;
    var paneW = 0;
    var paneH = 0;

    function measure() {
      rect = img.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        rect = null;
        return false;
      }

      zoom = clamp(
        (img.naturalWidth || rect.width) / rect.width,
        ZOOM_MIN,
        ZOOM_MAX,
      );

      // The pane never needs to be wider than the fully zoomed image, and it
      // has to leave room beside the panel plus a margin on both edges.
      var side = Math.max(rect.left, window.innerWidth - rect.right) - GAP * 2;
      paneW = Math.min(PANE_W, rect.width * zoom, side);
      paneH = Math.min(window.innerHeight * PANE_H_VH, rect.height * zoom);
      pane.style.width = paneW + "px";
      pane.style.height = paneH + "px";
      pane.style.backgroundSize =
        rect.width * zoom + "px " + rect.height * zoom + "px";

      // Prefer the right of the panel; fall back to the left when it fits
      // better there.
      var left = rect.right + GAP;
      if (left + paneW > window.innerWidth - GAP) left = rect.left - GAP - paneW;
      pane.style.left = clamp(left, GAP, window.innerWidth - paneW - GAP) + "px";
      pane.style.top =
        clamp(
          rect.top + rect.height / 2 - paneH / 2,
          GAP,
          window.innerHeight - paneH - GAP,
        ) + "px";
      return true;
    }

    function show(on) {
      marker.classList.toggle("is-on", on);
      pane.classList.toggle("is-on", on);
    }

    function move(e) {
      if (!rect && !measure()) return;

      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      if (x < 0 || y < 0 || x > rect.width || y > rect.height) {
        show(false);
        return;
      }
      show(true);

      // Slice of the source image the pane can hold, centred on the cursor and
      // kept inside the image.
      var sliceW = paneW / zoom;
      var sliceH = paneH / zoom;
      var sx = clamp(x - sliceW / 2, 0, Math.max(0, rect.width - sliceW));
      var sy = clamp(y - sliceH / 2, 0, Math.max(0, rect.height - sliceH));

      pane.style.backgroundPosition = -(sx * zoom) + "px " + -(sy * zoom) + "px";

      // Marker is positioned against the panel box, not the image.
      var boxRect = box.getBoundingClientRect();
      marker.style.left = rect.left - boxRect.left + sx + "px";
      marker.style.top = rect.top - boxRect.top + sy + "px";
      marker.style.width = Math.min(sliceW, rect.width) + "px";
      marker.style.height = Math.min(sliceH, rect.height) + "px";
    }

    function reset() {
      show(false);
      rect = null;
    }

    box.addEventListener("mouseenter", function (e) {
      measure();
      move(e);
    });
    box.addEventListener("mousemove", move);
    box.addEventListener("mouseleave", reset);
    window.addEventListener("resize", reset);
    window.addEventListener("scroll", reset, { passive: true });
  }

  function init() {
    if (!fine()) return;
    var boxes = document.querySelectorAll("[data-zoom]");
    for (var i = 0; i < boxes.length; i++) attach(boxes[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
