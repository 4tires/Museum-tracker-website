// Tooltips for the "?" note icons (see the note() macro in templates/macros.html).
//
// One shared tooltip element is positioned with position: fixed, so it is not
// clipped by scrollable tables (.table-scroll has overflow-x: auto). It shows
// on hover and on keyboard focus; tapping an icon focuses it, which covers
// touch screens.
(function () {
  var tip = document.createElement("div");
  tip.className = "note-tooltip";
  tip.setAttribute("role", "tooltip");
  tip.hidden = true;
  document.body.appendChild(tip);

  function show(icon) {
    tip.textContent = icon.dataset.note;
    tip.hidden = false;

    var gap = 8;
    var rect = icon.getBoundingClientRect();
    var width = tip.offsetWidth;
    var height = tip.offsetHeight;

    // Centered above the icon, kept inside the window; below it if no room above.
    var left = rect.left + rect.width / 2 - width / 2;
    left = Math.max(gap, Math.min(left, window.innerWidth - width - gap));
    var top = rect.top - height - gap;
    if (top < gap) top = rect.bottom + gap;

    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }

  function hide() {
    tip.hidden = true;
  }

  function iconFrom(event) {
    return event.target.closest ? event.target.closest(".note") : null;
  }

  document.addEventListener("mouseover", function (e) {
    var icon = iconFrom(e);
    if (icon) show(icon);
  });
  document.addEventListener("mouseout", function (e) {
    if (iconFrom(e) && document.activeElement !== iconFrom(e)) hide();
  });
  document.addEventListener("focusin", function (e) {
    var icon = iconFrom(e);
    if (icon) show(icon);
  });
  document.addEventListener("focusout", function (e) {
    if (iconFrom(e)) hide();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hide();
  });
  window.addEventListener("scroll", hide, true);
})();
