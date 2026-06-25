(function () {
  "use strict";

  const OVERLAY_ID = "upload-loader-overlay";

  function crearOverlay() {
    if (document.getElementById(OVERLAY_ID)) return;

    const overlay = document.createElement("div");
    overlay.id = OVERLAY_ID;
    overlay.innerHTML = `
      <div class="upload-loader-box">
        <div class="upload-spinner"></div>
        <p class="upload-loader-title">Subiendo imágenes…</p>
        <p class="upload-loader-sub">Por favor espera, no cierres esta ventana.</p>
      </div>
    `;

    const style = document.createElement("style");
    style.textContent = `
      #${OVERLAY_ID} {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.65);
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(3px);
      }
      .upload-loader-box {
        background: #fff;
        border-radius: 12px;
        padding: 40px 50px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        min-width: 280px;
      }
      .upload-spinner {
        width: 52px;
        height: 52px;
        border: 5px solid #e0e0e0;
        border-top-color: #1a4b8c;
        border-radius: 50%;
        animation: upload-spin 0.8s linear infinite;
        margin: 0 auto 20px;
      }
      @keyframes upload-spin {
        to { transform: rotate(360deg); }
      }
      .upload-loader-title {
        font-size: 17px;
        font-weight: 700;
        color: #1a4b8c;
        margin: 0 0 6px;
      }
      .upload-loader-sub {
        font-size: 13px;
        color: #777;
        margin: 0;
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(overlay);
  }

  function tieneImagenesNuevas() {
    const inputs = document.querySelectorAll('input[type="file"]');
    for (const input of inputs) {
      if (input.files && input.files.length > 0) return true;
    }
    return false;
  }

  function interceptarFormulario() {
    // Todos los botones de submit del admin (Guardar, Guardar y continuar, etc.)
    const form = document.querySelector("#content-main form, form#changelist-form, form.change-form");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      if (!tieneImagenesNuevas()) return; // sin archivos nuevos, no bloquear

      // Bloquear todos los botones para evitar doble envío
      form.querySelectorAll('input[type="submit"], button[type="submit"]').forEach(btn => {
        btn.disabled = true;
      });

      crearOverlay();
    });
  }

  // También interceptar clicks directos en botones submit (por si acaso)
  document.addEventListener("click", function (e) {
    const btn = e.target.closest('input[type="submit"], button[type="submit"]');
    if (!btn) return;
    const form = btn.closest("form");
    if (!form) return;
    if (!tieneImagenesNuevas()) return;

    // Si ya está mostrando el overlay, ignorar
    if (document.getElementById(OVERLAY_ID)) return;
    crearOverlay();
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", interceptarFormulario);
  } else {
    interceptarFormulario();
  }
})();
