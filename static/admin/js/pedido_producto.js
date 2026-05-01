(function ($) {
    'use strict';

    function rellenarDesdeFigura(figuraId) {
        if (!figuraId) return;
        fetch('/api/v1/figuras/' + figuraId + '/', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var grPieza      = document.getElementById('id_gr_pieza');
                var precioUnidad = document.getElementById('id_precio_unidad');
                if (grPieza)      grPieza.value      = 0;
                if (precioUnidad) precioUnidad.value  = d.precio_total;
            });
    }

    function limpiarCampos() {
        var grPieza      = document.getElementById('id_gr_pieza');
        var precioUnidad = document.getElementById('id_precio_unidad');
        if (grPieza)      grPieza.value      = '';
        if (precioUnidad) precioUnidad.value  = '';
    }

    $(document).ready(function () {
        if ($('#id_figura').val()) rellenarDesdeFigura($('#id_figura').val());

        $(document).on('select2:select', '#id_figura', function (e) { rellenarDesdeFigura(e.params.data.id); });
        $(document).on('select2:clear',  '#id_figura', limpiarCampos);
    });

}(django.jQuery));
