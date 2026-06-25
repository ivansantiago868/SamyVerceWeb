FROM python:3.13-slim

# Evitar prompts interactivos durante apt-get
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copiar todo el código fuente
COPY . .

# collectstatic no necesita BD ni credenciales reales, solo que SECRET_KEY exista
ENV DJANGO_SETTINGS_MODULE=config.settings.production
RUN SECRET_KEY=build-time-placeholder python manage.py collectstatic --noinput

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
