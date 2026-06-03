import json
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.conf import settings
from google import genai


@staff_member_required
@require_POST
def generar_descripcion_ia(request):
    data = json.loads(request.body)
    prompt = data.get("prompt", "").strip()
    nombre = data.get("nombre", "").strip()

    if not prompt:
        return JsonResponse({"error": "El prompt no puede estar vacío."}, status=400)

    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return JsonResponse({"error": "GEMINI_API_KEY no configurada."}, status=500)

    try:
        client = genai.Client(api_key=api_key)
        instruccion = (
            f"Eres un redactor de catálogo de productos de impresión 3D. "
            f"Escribe una descripción comercial atractiva para el producto llamado '{nombre}'. "
            f"Tema o palabras clave: {prompt}. "
            f"La descripción debe ser concisa (2-4 oraciones), resaltar características y uso, "
            f"en español, sin usar asteriscos ni markdown."
        )
        respuesta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=instruccion,
        )
        texto = respuesta.text.strip()
        return JsonResponse({"descripcion": texto})
    except Exception as exc:
        return JsonResponse({"error": str(exc)[:200]}, status=500)
