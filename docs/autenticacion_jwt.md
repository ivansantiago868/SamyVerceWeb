# Autenticación JWT

Este proyecto usa **JSON Web Tokens (JWT)** a través de la librería `djangorestframework-simplejwt`. Todos los endpoints de `/api/v1/` requieren un token válido para funcionar.

---

## ¿Qué es un JWT?

Un JWT es una cadena de texto codificada en Base64 dividida en tres partes separadas por puntos:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   ← Header
.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MDAwMDB9  ← Payload
.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV    ← Firma
```

- **Header** — algoritmo usado (HS256).
- **Payload** — datos del usuario y fechas de expiración. No está encriptado, solo codificado.
- **Firma** — garantiza que nadie manipuló el token. Se genera con el `SECRET_KEY` del servidor.

---

## Los dos tokens

El sistema maneja dos tipos de token con propósitos distintos:

| Token | Duración | Para qué sirve |
|-------|----------|----------------|
| `access` | 60 minutos | Autenticar cada petición a la API |
| `refresh` | 7 días | Obtener un nuevo `access` cuando expira |

### Access token

Se envía en cada petición al header `Authorization`:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Vive poco tiempo (60 min) para reducir el riesgo si alguien lo intercepta.

### Refresh token

Se guarda de forma segura en el cliente (por ejemplo en `localStorage` o una cookie `httpOnly`). Solo se usa para pedir un nuevo `access` cuando este expira. Vive 7 días.

Cuando se usa un refresh token para renovar, el sistema lo **rota**: invalida el anterior y emite uno nuevo. Esto evita que un token robado pueda usarse indefinidamente.

---

## Flujo completo

```
Usuario                        Servidor
  │                               │
  │  POST /api/auth/token/        │
  │  { username, password }  ──►  │  Verifica credenciales
  │                               │  Genera access (60 min) + refresh (7 días)
  │  ◄── { access, refresh }      │
  │                               │
  │  GET /api/v1/pedidos/         │
  │  Authorization: Bearer access ──►  Valida firma y expiración
  │  ◄── 200 OK { datos }         │
  │                               │
  │  (60 minutos después)         │
  │                               │
  │  POST /api/auth/token/refresh/│
  │  { refresh }  ──►             │  Valida refresh, rota tokens
  │  ◄── { access (nuevo) }       │
  │                               │
  │  POST /api/auth/logout/       │
  │  { refresh }  ──►             │  Agrega refresh a blacklist
  │  ◄── 200 OK                   │
```

---

## Endpoints

### Registro

```
POST /api/auth/registro/
```

No requiere autenticación. Crea un usuario y devuelve los dos tokens directamente.

**Body:**
```json
{
  "username": "samy",
  "email": "samy@correo.com",
  "first_name": "Samy",
  "last_name": "Verce",
  "password": "MiPassword123!",
  "password2": "MiPassword123!"
}
```

**Respuesta `201`:**
```json
{
  "mensaje": "Usuario 'samy' creado exitosamente.",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "usuario": {
    "id": 2,
    "username": "samy",
    "email": "samy@correo.com",
    "first_name": "Samy",
    "last_name": "Verce"
  }
}
```

---

### Login

```
POST /api/auth/token/
```

No requiere autenticación.

**Body:**
```json
{
  "username": "samy",
  "password": "MiPassword123!"
}
```

**Respuesta `200`:**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

---

### Renovar access token

```
POST /api/auth/token/refresh/
```

No requiere autenticación. Úsalo cuando el `access` expire (error `401 token_not_valid`).

**Body:**
```json
{
  "refresh": "eyJ..."
}
```

**Respuesta `200`:**
```json
{
  "access": "eyJ... (nuevo)"
}
```

> El refresh token anterior queda invalidado y se emite uno nuevo automáticamente (rotación).

---

### Verificar token

```
POST /api/auth/token/verify/
```

Útil para comprobar si un token sigue siendo válido sin hacer una petición real a la API.

**Body:**
```json
{
  "token": "eyJ..."
}
```

**Respuesta `200`:** el token es válido.  
**Respuesta `401`:** expirado o manipulado.

---

### Logout

```
POST /api/auth/logout/
Authorization: Bearer <access_token>
```

Agrega el refresh token a la **blacklist**, invalidándolo permanentemente. Después del logout el usuario debe hacer login de nuevo para obtener tokens nuevos.

**Body:**
```json
{
  "refresh": "eyJ..."
}
```

**Respuesta `200`:**
```json
{
  "mensaje": "Sesión cerrada correctamente."
}
```

---

### Ver / editar perfil

```
GET   /api/auth/perfil/
PATCH /api/auth/perfil/
Authorization: Bearer <access_token>
```

**Respuesta GET `200`:**
```json
{
  "id": 1,
  "username": "kivandy",
  "email": "",
  "first_name": "",
  "last_name": "",
  "date_joined": "2024-01-01T00:00:00Z",
  "last_login": "2024-06-01T10:30:00Z"
}
```

---

## Errores comunes

| Código | Mensaje | Causa | Solución |
|--------|---------|-------|----------|
| `401` | `Authentication credentials were not provided` | No se envió el header `Authorization` | Agregar `Authorization: Bearer <token>` |
| `401` | `token_not_valid` | El access token expiró | Renovar con `POST /api/auth/token/refresh/` |
| `401` | `Token is blacklisted` | Se hizo logout con ese refresh token | Volver a hacer login |
| `401` | `No active account found` | Usuario o contraseña incorrectos | Verificar credenciales |
| `400` | `This field is required` | Faltó un campo en el body | Revisar el body de la petición |

---

## Configuración actual

Los tiempos de expiración se controlan desde el archivo `.env`:

```env
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60   # access expira en 60 minutos
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7      # refresh expira en 7 días
```

Y se aplican en `config/settings/base.py`:

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":    timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME":   timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":    True,   # rota el refresh en cada uso
    "BLACKLIST_AFTER_ROTATION": True,   # invalida el anterior tras rotar
    "AUTH_HEADER_TYPES":        ("Bearer",),
}
```
