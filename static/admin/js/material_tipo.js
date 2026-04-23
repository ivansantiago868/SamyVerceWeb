(function () {
    'use strict';

    var TIPOS = {
        FDM: [
            "PLA", "PETG", "TPU_TPE", "ABS", "ASA", "Nylon", "PC", "Especial"
        ],
        Resina: [
            "R_Estandar", "R_WW", "R_ABS", "R_Flex", "R_Clear",
            "R_Castable", "R_HiTemp", "R_Eco", "R_Fast", "R_Dental"
        ]
    };

    function filtrarTipos(categoriaSelect, tipoSelect) {
        var categoria = categoriaSelect.value;
        var permitidos = TIPOS[categoria] || [];
        var valorActual = tipoSelect.value;

        Array.prototype.forEach.call(tipoSelect.options, function (opt) {
            if (opt.value === '') {
                opt.hidden = false;
                return;
            }
            opt.hidden = permitidos.length > 0 && permitidos.indexOf(opt.value) === -1;
        });

        // Si el valor actual ya no aplica, limpiar
        if (valorActual && permitidos.indexOf(valorActual) === -1) {
            tipoSelect.value = '';
        }
    }

    function iniciar(prefix) {
        prefix = prefix || '';
        var catId  = prefix ? 'id_' + prefix + '-categoria' : 'id_categoria';
        var tipoId = prefix ? 'id_' + prefix + '-tipo'      : 'id_tipo';

        var categoriaSelect = document.getElementById(catId);
        var tipoSelect      = document.getElementById(tipoId);

        if (!categoriaSelect || !tipoSelect) return;

        filtrarTipos(categoriaSelect, tipoSelect);

        categoriaSelect.addEventListener('change', function () {
            filtrarTipos(categoriaSelect, tipoSelect);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        iniciar();
    });
}());
