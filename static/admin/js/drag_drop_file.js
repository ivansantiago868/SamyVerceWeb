document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".drag-drop-input").forEach(initDragDrop);
  document.querySelectorAll(".drag-drop-img-input").forEach(initDragDropImage);
});

/* ── Widget genérico (archivos) ───────────────────────────── */
function initDragDrop(input) {
  const wrapper = input.closest(".drag-drop-wrapper");
  if (!wrapper) return;

  const zone        = wrapper.querySelector(".drag-drop-zone");
  const preview     = wrapper.querySelector(".drag-drop-preview");
  const previewName = wrapper.querySelector(".drag-drop-preview-name");
  const clearBtn    = wrapper.querySelector(".drag-drop-clear");

  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  input.addEventListener("change", () => {
    if (input.files[0]) setFile(input.files[0]);
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      input.value = "";
      preview.style.display = "none";
      zone.style.display = "flex";
      const clearCheck = wrapper.querySelector("input[type='checkbox']");
      if (clearCheck) clearCheck.checked = true;
    });
  }

  function setFile(file) {
    if (!input.files.length || input.files[0] !== file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    }
    previewName.textContent = file.name;
    preview.style.display = "flex";
    zone.style.display = "none";
  }
}

/* ── Widget de imagen (con previsualización) ──────────────── */
function initDragDropImage(input) {
  const wrapper     = input.closest(".drag-drop-wrapper");
  if (!wrapper) return;

  const zone        = wrapper.querySelector(".drag-drop-zone");
  const imgPreview  = wrapper.querySelector(".drag-drop-img-preview");
  const imgEl       = imgPreview ? imgPreview.querySelector("img") : null;
  const previewName = wrapper.querySelector(".drag-drop-preview-name");
  const clearBtn    = wrapper.querySelector(".drag-drop-clear");

  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) setImage(file);
  });

  input.addEventListener("change", () => {
    if (input.files[0]) setImage(input.files[0]);
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      input.value = "";
      if (imgEl) { imgEl.src = ""; }
      if (imgPreview) imgPreview.style.display = "none";
      zone.style.display = "flex";
      const clearCheck = wrapper.querySelector("input[type='checkbox']");
      if (clearCheck) clearCheck.checked = true;
    });
  }

  function setImage(file) {
    if (!input.files.length || input.files[0] !== file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      if (imgEl) imgEl.src = ev.target.result;
      if (previewName) previewName.textContent = file.name;
      if (imgPreview) imgPreview.style.display = "block";
      zone.style.display = "none";
    };
    reader.readAsDataURL(file);
  }
}
