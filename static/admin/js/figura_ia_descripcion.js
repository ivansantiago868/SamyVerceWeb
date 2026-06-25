document.addEventListener("DOMContentLoaded", function () {
  const btnGenerar = document.getElementById("btn-generar-descripcion");
  if (!btnGenerar) return;

  btnGenerar.addEventListener("click", async function () {
    const promptInput = document.getElementById("id_prompt_ia");
    const descripcionField = document.getElementById("id_descripcion");
    const nombreField = document.getElementById("id_nombre");
    const statusEl = document.getElementById("ia-status");

    const prompt = promptInput ? promptInput.value.trim() : "";
    const nombre = nombreField ? nombreField.value.trim() : "";

    if (!prompt) {
      statusEl.textContent = "⚠ Escribe un tema o palabras clave primero.";
      statusEl.style.color = "#c0392b";
      return;
    }

    btnGenerar.disabled = true;
    btnGenerar.textContent = "⏳ Generando…";
    statusEl.textContent = "";

    try {
      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
      const resp = await fetch("/admin/produccion/figura/generar-descripcion-ia/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ prompt, nombre }),
      });

      const data = await resp.json();

      if (data.descripcion) {
        descripcionField.value = data.descripcion;
        statusEl.textContent = "✓ Descripción generada.";
        statusEl.style.color = "#27ae60";
      } else {
        statusEl.textContent = "✗ " + (data.error || "Error desconocido.");
        statusEl.style.color = "#c0392b";
      }
    } catch (e) {
      statusEl.textContent = "✗ Error de red.";
      statusEl.style.color = "#c0392b";
    } finally {
      btnGenerar.disabled = false;
      btnGenerar.textContent = "✨ Generar con IA";
    }
  });
});
