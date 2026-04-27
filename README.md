# 🖨️ Sistema de Gestión de Impresión 3D — Django REST API (MVC + JWT)

Sistema de gestión para negocios de impresión 3D con arquitectura **Modelo–Vista–Controlador**, autenticación **JWT** y base de datos **PostgreSQL**.

---

## 📁 Estructura del Proyecto (MVC)

```
├── config/
│   ├── settings/
│   │   ├── base.py           ← Configuración común (DB, JWT, DRF)
│   │   ├── development.py    ← DEBUG=True + debug_toolbar
│   │   └── production.py     ← DEBUG=False + cabeceras de seguridad
│   ├── urls.py               ← Rutas globales (auth + api/v1/)
│   └── wsgi.py
│
├── apps/
│   └── produccion/
│       │
│       ├── models/           ◄── MODELO — estructura de datos
│       │   ├── cliente.py
│       │   ├── impresora.py
│       │   ├── insumo.py
│       │   ├── gasto.py
│       │   ├── variables_fijas.py
│       │   ├── inventario_pieza.py
│       │   ├── pedido.py
│       │   ├── venta_tarea.py
│       │   └── __init__.py   ← exporta todos los modelos
│       │
│       ├── controllers/      ◄── CONTROLADOR — serializers + lógica de negocio
│       │   ├── auth_controller.py          ← registro, logout, perfil
│       │   ├── cliente_controller.py
│       │   ├── impresora_controller.py
│       │   ├── insumo_controller.py
│       │   ├── gasto_controller.py
│       │   ├── variables_fijas_controller.py
│       │   ├── inventario_controller.py
│       │   ├── pedido_controller.py
│       │   ├── venta_controller.py
│       │   ├── tarea_controller.py
│       │   ├── cotizador_controller.py     ← orquesta el cotizador
│       │   └── __init__.py   ← exporta todo
│       │
│       ├── views/            ◄── VISTA — respuestas HTTP (solo enruta y responde)
│       │   ├── recursos_view.py    ← Cliente, Impresora, Insumo, Gasto
│       │   ├── produccion_view.py  ← VariablesFijas, Piezas, Pedido, Venta, Tarea
│       │   ├── cotizador_view.py   ← 4 endpoints del cotizador
│       │   └── __init__.py
│       │
│       ├── services/         ← Lógica pura sin HTTP ni ORM (fórmulas del cotizador)
│       │   └── cotizador.py
│       │
│       ├── tests/
│       │   └── test_cotizador.py
│       │
│       ├── migrations/
│       │   └── 0001_initial.py   ← crea las 9 tablas del sistema
│       │
│       ├── management/commands/
│       │   └── importar_excel.py
│       │
│       ├── urls.py           ← Router CRUD + rutas del cotizador
│       ├── admin.py
│       └── apps.py
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── .env                      ← Variables de entorno reales (NO subir a Git)
├── .env.example              ← Plantilla pública
├── manage.py
├── Dockerfile
└── docker-compose.yml
```

---

## ⚙️ Requisitos

| Herramienta | Versión mínima |
|-------------|---------------|
| Python      | 3.13          |
| PostgreSQL   | 14+           |
| pip         | 23+           |

---

## 🚀 Instalación local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo
```

### 2. Crear entorno virtual

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements/development.txt
```

### 4. Variables de entorno

El archivo `.env` ya viene configurado con los datos reales de la base de datos:

```env
SECRET_KEY=django-insecure-cambia-esto-en-produccion-usa-una-clave-larga
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=Kivandy1920
DB_HOST=localhost
DB_PORT=5432

JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

DJANGO_SETTINGS_MODULE=config.settings.development
```

> ⚠️ Para producción, cambia `SECRET_KEY` por una clave larga y aleatoria:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 5. Aplicar migraciones

Las migraciones ya están incluidas en el repositorio (`apps/produccion/migrations/0001_initial.py`), por lo que solo es necesario aplicarlas:

```bash
python manage.py migrate
```

> Si agregas o modificas modelos en el futuro, genera la nueva migración antes de aplicarla:
> ```bash
> python manage.py makemigrations
> python manage.py migrate
> ```

### 6. Crear superusuario (admin)

```bash
python manage.py createsuperuser
```

### 7. Importar datos del Excel

```bash
python manage.py importar_excel --archivo ruta/al/Calculos_Contabilidad_Samy_Verce.xlsm
```

### 8. Levantar el servidor

```bash
python manage.py runserver
```

---

## 🔐 Autenticación JWT

Todos los endpoints de `/api/v1/` requieren un **Bearer Token** en el header:

```
Authorization: Bearer <access_token>
```

### Flujo completo

#### 1. Registrar usuario
```bash
POST /api/auth/registro/

{
  "username": "samy",
  "email": "samy@correo.com",
  "first_name": "Samy",
  "last_name": "Verce",
  "password": "MiPassword123!",
  "password2": "MiPassword123!"
}
```
**Respuesta:**
```json
{
  "mensaje": "Usuario 'samy' creado exitosamente.",
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

#### 2. Login (obtener tokens)
```bash
POST /api/auth/token/

{
  "username": "samy",
  "password": "MiPassword123!"
}
```
**Respuesta:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 3. Usar el access token en cada petición
```bash
GET /api/v1/pedidos/
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 4. Renovar access token (cuando expira)
```bash
POST /api/auth/token/refresh/

{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 5. Verificar si un token es válido
```bash
POST /api/auth/token/verify/

{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 6. Logout (revocar refresh token)
```bash
POST /api/auth/logout/
Authorization: Bearer <access_token>

{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 7. Ver / actualizar perfil
```bash
GET   /api/auth/perfil/
PATCH /api/auth/perfil/
Authorization: Bearer <access_token>
```

---

## 🔌 Endpoints de la API

### Autenticación

| Método | URL | Descripción | Auth |
|--------|-----|-------------|------|
| POST | `/api/auth/registro/` | Registrar nuevo usuario | ❌ |
| POST | `/api/auth/token/` | Login → obtener tokens | ❌ |
| POST | `/api/auth/token/refresh/` | Renovar access token | ❌ |
| POST | `/api/auth/token/verify/` | Verificar token | ❌ |
| POST | `/api/auth/logout/` | Revocar refresh token | ✅ |
| GET/PATCH | `/api/auth/perfil/` | Ver / editar perfil | ✅ |

### Recursos CRUD

| Método | URL | Descripción |
|--------|-----|-------------|
| GET/POST | `/api/v1/clientes/` | Listar / Crear |
| GET/PUT/PATCH/DELETE | `/api/v1/clientes/{id}/` | Detalle / Editar / Eliminar |
| GET/POST | `/api/v1/impresoras/` | Listar / Crear |
| GET | `/api/v1/impresoras/activas/` | Solo impresoras activas |
| GET/POST | `/api/v1/insumos/` | Listar / Crear |
| GET | `/api/v1/insumos/stock-critico/` | Insumos con menos de 100g |
| GET/POST | `/api/v1/gastos/` | Listar / Crear |
| GET | `/api/v1/gastos/resumen/` | Total gastado y compras |
| GET/PATCH | `/api/v1/variables-fijas/1/` | Ver / Actualizar configuración |
| GET/POST | `/api/v1/piezas/` | Listar / Crear piezas |
| GET/POST | `/api/v1/pedidos/` | Listar / Crear pedidos |
| GET | `/api/v1/pedidos/dashboard/` | Resumen por estado y prioridad |
| PATCH | `/api/v1/pedidos/{id}/cambiar-estado/` | Cambiar estado del pedido |
| GET/POST | `/api/v1/ventas/` | Listar / Crear ventas |
| GET | `/api/v1/ventas/resumen/` | Total ventas y unidades |
| GET/POST | `/api/v1/tareas/` | Listar / Crear tareas |
| GET | `/api/v1/tareas/pendientes/` | Tareas pendientes y en cola |
| PATCH | `/api/v1/tareas/{id}/cambiar-estado/` | Cambiar estado de tarea |

### Cotizador

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/v1/cotizador/` | Cotizar pieza nueva |
| POST | `/api/v1/cotizador/lote/` | Cotizar pieza nueva × cantidad |
| POST | `/api/v1/cotizador/desde-catalogo/` | Recalcular pieza del catálogo |
| POST | `/api/v1/cotizador/desde-catalogo/lote/` | Recalcular pieza del catálogo × cantidad |

---

## 🐳 Docker

### Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt requirements/production.txt
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .

EXPOSE 8000
```

### docker-compose.yml

```yaml
version: "3.9"

services:
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: Kivandy1920
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    restart: always
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

volumes:
  postgres_data:
```

### Comandos Docker

```bash
# Construir y levantar
docker compose up --build

# En segundo plano
docker compose up -d --build

# Migraciones
docker compose exec web python manage.py migrate

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Importar Excel
docker compose exec web python manage.py importar_excel \
  --archivo /app/Calculos_Contabilidad_Samy_Verce.xlsm

# Ver logs
docker compose logs -f web

# Detener
docker compose down
```

---

## 🧪 Tests

```bash
# Todos los tests
python manage.py test

# Solo el cotizador (16 casos verificados contra Excel)
python manage.py test apps.produccion.tests.test_cotizador --verbosity=2

# Con cobertura
coverage run manage.py test
coverage report
coverage html
```


## eliminar data 

# Ver cuántos registros hay (sin borrar)
python manage.py limpiar_datos

# Borrar todo (pide confirmación manual)
python manage.py limpiar_datos --confirmar

# Solo los datos de la empresa ID=1
python manage.py limpiar_datos --empresa 1 --confirmar

# Incluir también clientes e impresoras
python manage.py limpiar_datos --todo --confirmar

---

## 🛠️ Solución de problemas

**`could not connect to server` (PostgreSQL)**
→ Verificar que PostgreSQL esté corriendo en `localhost:5432` con usuario `postgres` y contraseña `Kivandy1920`.

**`ModuleNotFoundError: No module named 'rest_framework_simplejwt'`**
→ Ejecutar `pip install djangorestframework-simplejwt`

**`401 Unauthorized` en los endpoints**
→ Incluir el header: `Authorization: Bearer <tu_access_token>`

**`401` con mensaje `token_not_valid`**
→ El access token expiró (60 min). Renovarlo con `POST /api/auth/token/refresh/`

**El cotizador responde `424 FAILED DEPENDENCY`**
→ Crear las Variables Fijas primero:
```bash
python manage.py importar_excel --archivo tu_archivo.xlsm
```

**`Token is blacklisted`**
→ Ya se hizo logout con ese refresh token. Volver a hacer login para obtener tokens nuevos.
