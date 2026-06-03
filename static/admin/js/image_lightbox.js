(function () {
  "use strict";

  const ID = "sv-lightbox";

  function buildLightbox() {
    if (document.getElementById(ID)) return;

    const overlay = document.createElement("div");
    overlay.id = ID;
    overlay.innerHTML = `
      <div class="sv-lb-backdrop"></div>
      <div class="sv-lb-box">
        <button class="sv-lb-close" aria-label="Cerrar">&#x2715;</button>
        <img class="sv-lb-img" src="" alt="Vista ampliada">
      </div>
    `;

    const style = document.createElement("style");
    style.textContent = `
      #${ID} {
        display: none;
        position: fixed;
        inset: 0;
        z-index: 99999;
        align-items: center;
        justify-content: center;
      }
      #${ID}.sv-lb-open { display: flex; }
      .sv-lb-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,.82);
        backdrop-filter: blur(4px);
        cursor: zoom-out;
      }
      .sv-lb-box {
        position: relative;
        z-index: 1;
        max-width: 92vw;
        max-height: 92vh;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: sv-lb-in .18s ease;
      }
      @keyframes sv-lb-in {
        from { opacity:0; transform: scale(.93); }
        to   { opacity:1; transform: scale(1); }
      }
      .sv-lb-img {
        max-width: 90vw;
        max-height: 88vh;
        border-radius: 8px;
        box-shadow: 0 8px 40px rgba(0,0,0,.6);
        object-fit: contain;
        display: block;
      }
      .sv-lb-close {
        position: absolute;
        top: -14px;
        right: -14px;
        background: #fff;
        border: none;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,.35);
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
        color: #333;
        z-index: 2;
      }
      .sv-lb-close:hover { background: #f0f0f0; }
    `;

    document.head.appendChild(style);
    document.body.appendChild(overlay);

    const img   = overlay.querySelector(".sv-lb-img");
    const close = overlay.querySelector(".sv-lb-close");
    const backdrop = overlay.querySelector(".sv-lb-backdrop");

    function open(src) {
      img.src = src;
      overlay.classList.add("sv-lb-open");
      document.body.style.overflow = "hidden";
    }

    function closeLb() {
      overlay.classList.remove("sv-lb-open");
      document.body.style.overflow = "";
      img.src = "";
    }

    close.addEventListener("click", closeLb);
    backdrop.addEventListener("click", closeLb);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeLb();
    });

    // Exponer para uso global
    window._svLightbox = { open };
  }

  function interceptClicks() {
    // Miniaturas en el list_display — abrir en lightbox al hacer click
    document.querySelectorAll(
      ".field-miniatura img, .field-miniatura_ia img, " +
      ".field-preview_ia img, .field-carrusel_imagenes img, .field-carrusel_ia img"
    ).forEach((img) => {
      if (img.dataset.lbBound) return;
      img.dataset.lbBound = "1";
      img.style.cursor = "zoom-in";
      img.addEventListener("click", () => window._svLightbox.open(img.src));
    });
  }

  function init() {
    buildLightbox();
    interceptClicks();
    // Re-interceptar cuando el admin actualiza el DOM (inline dinámico)
    new MutationObserver(interceptClicks).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
