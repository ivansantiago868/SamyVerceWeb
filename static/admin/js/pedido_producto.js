document.addEventListener('DOMContentLoaded', function () {
    'use strict';
    // django.jQuery solo existe una vez que jquery.init.js corrió; este script
    // se carga antes en el <head>, así que no se puede leer django.jQuery al
    // nivel superior (rompía todo el archivo con "$ is not a function").
    var $ = django.jQuery;

    function poblarSelect(select, opciones) {
        if (!select) return;
        var valorActual = select.value;
        select.innerHTML = '';
        var vacia = document.createElement('option');
        vacia.value = '';
        vacia.textContent = '---------';
        select.appendChild(vacia);
        opciones.forEach(function (op) {
            var opt = document.createElement('option');
            opt.value = op.id;
            opt.textContent = op.nombre;
            select.appendChild(opt);
        });
        var sigueValido = opciones.some(function (op) { return String(op.id) === valorActual; });
        select.value = sigueValido ? valorActual : '';
    }

    function rellenarDesdeFigura(figuraId) {
        if (!figuraId) return;
        fetch('/api/v1/figuras/' + figuraId + '/', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var grPieza      = document.getElementById('id_gr_pieza');
                var precioUnidad = document.getElementById('id_precio_unidad');
                if (grPieza)      grPieza.value      = 0;
                if (precioUnidad) precioUnidad.value  = d.precio_total;
                poblarSelect(document.getElementById('id_color'), d.colores || []);
                poblarSelect(document.getElementById('id_tipo'), d.tipos || []);
            });
    }

    function limpiarCampos() {
        var grPieza      = document.getElementById('id_gr_pieza');
        var precioUnidad = document.getElementById('id_precio_unidad');
        if (grPieza)      grPieza.value      = '';
        if (precioUnidad) precioUnidad.value  = '';
        poblarSelect(document.getElementById('id_color'), []);
        poblarSelect(document.getElementById('id_tipo'), []);
    }

    function conMiniatura(data) {
        if (!data.id || !data.img) return data.text;
        var $item = $(
            '<span style="display:flex;align-items:center;gap:8px">' +
            '<img style="width:34px;height:34px;object-fit:cover;border-radius:4px;flex-shrink:0">' +
            '<span></span>' +
            '</span>'
        );
        $item.find('img').attr('src', data.img);
        $item.find('span').text(data.text);
        return $item;
    }

    function activarMiniaturas() {
        var $figura = $('#id_figura');
        var data    = $figura.data('select2');
        if (!data) return;
        data.options.options.templateResult    = conMiniatura;
        data.options.options.templateSelection = conMiniatura;
    }

    if ($('#id_figura').val()) rellenarDesdeFigura($('#id_figura').val());

    $(document).on('select2:select', '#id_figura', function (e) { rellenarDesdeFigura(e.params.data.id); });
    $(document).on('select2:clear',  '#id_figura', limpiarCampos);

    // Aunque ya pasó DOMContentLoaded, autocomplete.js inicializa select2 en su
    // propio handler jQuery "ready"; con setTimeout(0) nos aseguramos de correr
    // después de que termine (los listeners de un mismo evento corren en orden
    // de registro, y setTimeout solo se procesa cuando todos ya terminaron).
    setTimeout(activarMiniaturas, 0);
});
