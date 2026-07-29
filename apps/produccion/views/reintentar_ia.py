from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseNotAllowed, JsonResponse

from apps.produccion.models.figura import FiguraImagen
from apps.produccion.services.vertex_imagen import procesar_en_background
from apps.produccion.views.pdf_catalogo_figuras import _qs_y_empresa


def _fallidas_qs(request):
    figuras, _nombre_empresa, _empresa, _categoria = _qs_y_empresa(request)
    return FiguraImagen.objects.filter(figura__in=figuras).exclude(ia_error="")


@staff_member_required
def conteo_ia_fallidas(request):
    """Cuántas imágenes de figuras tienen actualmente error de procesamiento IA."""
    total = _fallidas_qs(request).count()
    return JsonResponse({"total": total})


@staff_member_required
def reintentar_ia_fallidas(request):
    """Relanza el procesamiento IA de todas las imágenes de figuras que quedaron
    con error (respeta el alcance de empresa del usuario). Devuelve los IDs
    relanzados para que el frontend pueda seguir el progreso."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    fallidas = list(_fallidas_qs(request).select_related("figura"))

    ids = []
    for img in fallidas:
        if not img.imagen:
            continue
        FiguraImagen.objects.filter(pk=img.pk).update(ia_error="")
        procesar_en_background(FiguraImagen, img.pk, img.imagen.url)
        ids.append(img.pk)

    return JsonResponse({"ids": ids, "total": len(ids)})


@staff_member_required
def estado_ia_reintento(request):
    """Progreso de un lote de imágenes relanzadas: cuántas ya completaron,
    cuántas volvieron a fallar y cuántas siguen procesando."""
    ids_raw = request.GET.get("ids", "")
    ids = [int(pk) for pk in ids_raw.split(",") if pk.strip().isdigit()]
    if not ids:
        return JsonResponse({"total": 0, "completadas": 0, "fallidas": 0, "pendientes": 0})

    qs = FiguraImagen.objects.filter(pk__in=ids)
    completadas = 0
    fallidas = 0
    for img in qs:
        if img.imagen_procesada:
            completadas += 1
        elif img.ia_error:
            fallidas += 1

    total = len(ids)
    pendientes = total - completadas - fallidas
    return JsonResponse({
        "total": total,
        "completadas": completadas,
        "fallidas": fallidas,
        "pendientes": pendientes,
    })
