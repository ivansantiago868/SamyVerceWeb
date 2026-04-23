(function ($) {
    'use strict';

    function rellenarDesdePieza(piezaId) {
        if (!piezaId) return;

        fetch('/api/v1/piezas/' + piezaId + '/', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var grPieza      = document.getElementById('id_gr_pieza');
                var precioUnidad = document.getElementById('id_precio_unidad');
                if (grPieza)      grPieza.value      = d.peso_gramos;
                if (precioUnidad) precioUnidad.value  = d.precio_venta_sugerido;
            });
    }

    $(document).ready(function () {
        // Al cargar en modo edición, rellenar con la pieza ya seleccionada
        var selectProducto = $('#id_pieza');
        if (selectProducto.val()) {
            rellenarDesdePieza(selectProducto.val());
        }

        // Select2 dispara este evento al elegir un ítem del desplegable
        $(document).on('select2:select', '#id_pieza', function (e) {
            rellenarDesdePieza(e.params.data.id);
        });

        // Fallback: cuando se limpia la selección
        $(document).on('select2:clear', '#id_pieza', function () {
            var grPieza      = document.getElementById('id_gr_pieza');
            var precioUnidad = document.getElementById('id_precio_unidad');
            if (grPieza)      grPieza.value      = '';
            if (precioUnidad) precioUnidad.value  = '';
        });
    });

}(django.jQuery));
