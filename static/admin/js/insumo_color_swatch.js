(function () {
  function extraerColor(texto) {
    var m = /^#([0-9a-fA-F]{6})\b/.exec(texto || "");
    return m ? "#" + m[1] : null;
  }

  function conSwatch(data) {
    var $ = window.django.jQuery;
    var color = extraerColor(data.text);
    var $span = $("<span></span>");
    if (color) {
      $("<span></span>")
        .css({
          display: "inline-block",
          width: "12px",
          height: "12px",
          borderRadius: "50%",
          background: color,
          marginRight: "6px",
          border: "1px solid #999",
          verticalAlign: "middle",
        })
        .appendTo($span);
    }
    $span.append(document.createTextNode(data.text || data.id || ""));
    return $span;
  }

  function reinit($select) {
    // django.jQuery.fn.djangoAdminSelect2() ignora cualquier opción que se le pase
    // (usa siempre su propia config fija) — hay que llamar a select2() directo,
    // repitiendo el mismo mapeo de ajax.data que arma Django, para poder sumar
    // templateResult/templateSelection.
    if ($select.hasClass("select2-hidden-accessible")) {
      $select.select2("destroy");
    }
    var element = $select.get(0);
    $select.select2({
      ajax: {
        data: function (params) {
          return {
            term: params.term,
            page: params.page,
            app_label: element.dataset.appLabel,
            model_name: element.dataset.modelName,
            field_name: element.dataset.fieldName,
          };
        },
      },
      templateResult: conSwatch,
      templateSelection: conSwatch,
    });
  }

  function initTodos() {
    var $ = window.django.jQuery;
    $('select[id*="-insumo"]').each(function () {
      reinit($(this));
    });
  }

  function listo() {
    return (
      window.django &&
      typeof window.django.jQuery === "function" &&
      typeof window.django.jQuery.fn.select2 === "function"
    );
  }

  function esperar(intentos) {
    if (listo()) {
      initTodos();
      window.django.jQuery(document).on("formset:added", function () {
        setTimeout(initTodos, 50);
      });
      return;
    }
    if (intentos <= 0) {
      return;
    }
    setTimeout(function () {
      esperar(intentos - 1);
    }, 100);
  }

  function arrancar() {
    setTimeout(function () {
      esperar(50);
    }, 150);
  }

  if (document.readyState === "complete") {
    arrancar();
  } else {
    window.addEventListener("load", arrancar);
  }
})();
