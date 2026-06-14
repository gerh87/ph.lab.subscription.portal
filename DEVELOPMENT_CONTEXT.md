# LabSchool - Contexto de Desarrollo

Fecha de referencia: 2026-06-02

Este documento resume el estado actual del proyecto para retomar el desarrollo sin perder contexto.

## Objetivo Del Sistema

LabSchool es un portal para gestionar cursos online.

El sistema tiene dos frentes:

- **User front**: pantalla publica para usuarios externos. Permite ver cursos, autenticarse, crear perfil de suscriptor y suscribirse a cursos.
- **Backoffice/admin**: panel interno para administradores. Permite gestionar cursos, usuarios, suscriptores e inscripciones.

## Stack Actual

- Backend: FastAPI
- Frontend: Vue 3 + Vite
- Base de datos: SQL Server 2022
- Object storage: MinIO compatible S3
- Infra local: Docker Compose
- Reverse proxy local: nginx
- Auth actual: Auth0
- Validacion backend: OpenID Connect generico

## Docker

Servicios en `docker-compose.yml`:

- `sqlserver`: SQL Server en puerto `1433`
- `backend`: FastAPI en puerto interno `8000`, publicado en host como `8400`
- `frontend`: Vite en puerto interno `3000`, publicado en host como `8401`
- `nginx`: proxy en puerto `80`

La app principal se abre por:

```text
http://localhost
```

El frontend directo queda en:

```text
http://localhost:8401
```

La API directa queda en:

```text
http://localhost:8400
```

Comandos utiles:

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=80 backend
docker compose logs --tail=80 frontend
docker compose logs --tail=80 nginx
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

Cuando se recrea `frontend`, conviene reiniciar `nginx` porque puede cachear la IP vieja del upstream Docker y dar `502 Bad Gateway`:

```bash
docker compose restart nginx
```

## Estado De Migraciones

Migraciones existentes:

- `0001_initial.py`
- `0002_auth0_user_fields.py`
- `0003_subscriber_user_link.py`
- `0004_delete_cancelled_enrollments.py`
- `0005_course_scheduled_date.py`
- `0006_course_zoom_url.py`

Estado verificado:

```text
0006_course_zoom_url (head)
```

La tabla `courses` tiene actualmente:

- `scheduled_date`
- `zoom_url`

## Cursos

El modelo `Course` incluye:

- `title`
- `description`
- `price`
- `max_students`
- `scheduled_date`
- `zoom_url`
- `created_at`

La fecha de realizacion del curso se guarda en `scheduled_date`.

El link de clase virtual se guarda en `zoom_url`.

En el admin se puede cargar:

- titulo
- descripcion
- fecha del curso
- link de Zoom
- precio
- cupos

En el user front:

- se muestra la fecha del curso
- si no hay fecha, muestra `Date to be confirmed`
- si el usuario esta suscripto y la fecha del curso es hoy, aparece `Join Zoom class`

## Acceso Virtual / Zoom

Endpoint:

```text
GET /api/v1/enrollments/{id}/virtual-access
```

Reglas actuales:

- requiere usuario autenticado
- el usuario debe ser admin o dueño de la suscripcion
- la suscripcion debe estar `active`
- el curso debe tener `scheduled_date == date.today()`
- el curso debe tener `zoom_url`

Si todo se cumple, devuelve:

```json
{
  "zoom_url": "..."
}
```

## Storage De Archivos

Se definio usar MinIO/S3 para archivos de cursos.

Configuracion esperada en `.env`:

```env
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_REGION=us-east-1
S3_USE_SSL=true
```

El bucket configurado para LabSchool es:

```text
lbschool-course-files
```

No guardar binarios en SQL Server. La idea es:

- guardar archivos reales en MinIO
- guardar metadata en SQL Server
- subir cada archivo al bucket usando un GUID v4 como clave, sin extension
- registrar ese GUID en SQL Server para usarlo como referencia de descarga
- conservar el nombre original, tipo MIME, peso, checksum SHA-256, usuario uploader y fecha de subida

El backend tiene un cliente base en:

```text
backend/app/core/storage.py
```

Implementado en la migracion:

```text
backend/alembic/versions/0007_course_files.py
```

Tabla:

- `course_files.id`
- `course_files.course_id`
- `course_files.guid`
- `course_files.storage_key`
- `course_files.original_filename`
- `course_files.resource_type`
- `course_files.content_type`
- `course_files.size_bytes`
- `course_files.checksum_sha256`
- `course_files.uploaded_by_user_id`
- `course_files.created_at`

La migracion `0008_course_file_resource_type.py` agrega `resource_type`.

Por ahora, los archivos cargados desde el admin son:

```text
public_resource
```

Estos representan programas, folletos, guias o informacion publica del curso. Se muestran en las cards del user front y se pueden descargar sin estar suscripto.

Endpoints:

- `POST /api/v1/courses/{course_id}/files`: admin sube archivo
- `GET /api/v1/courses/{course_id}/files`: admin o usuario suscripto lista archivos
- `GET /api/v1/courses/{course_id}/files/{file_id}/download`: admin o usuario suscripto descarga
- `DELETE /api/v1/courses/{course_id}/files/{file_id}`: admin borra archivo
- `GET /api/v1/courses/{course_id}/resources`: publico, lista recursos con `resource_type = public_resource`
- `GET /api/v1/courses/{course_id}/resources/{file_id}/download`: publico, descarga recursos con `resource_type = public_resource`

En el frontend admin, la creacion de cursos se maneja con un wizard:

- contenido basico
- agenda, precio, cupos y link de Zoom
- cola de archivos/materiales

El wizard vive dentro de un modal abierto desde `New course`, para que `/admin/courses` quede enfocada en metricas, tabla y detalle del curso seleccionado. La edicion tambien se abre en modal.

Al confirmar, primero se crea el curso y luego se suben los archivos seleccionados usando el `course_id` generado. Si algun archivo falla, el curso queda creado y esos archivos permanecen en la cola para reintentar.

Reglas de acceso:

- admin puede subir, listar, descargar y borrar archivos de cualquier curso
- usuario normal solo puede listar y descargar archivos de cursos donde tiene inscripcion `active`
- usuario normal no puede subir ni borrar archivos

Pendiente posible:

- definir limites de tipo/tamaño de archivo por negocio

Nginx tiene `client_max_body_size 50m` para permitir uploads de materiales. Si se aumenta el limite de archivos en backend/frontend, revisar tambien este valor.

## Inscripciones

La logica de cancelacion fue cambiada.

Antes:

- se guardaba `status = cancelled`

Ahora:

- cancelar elimina la inscripcion de la base
- no se conserva historial de canceladas
- la migracion `0004_delete_cancelled_enrollments.py` borra registros existentes con `status = 'cancelled'`

Esto fue decidido porque, por ahora, el negocio no necesita conservar bajas historicas.

## Cupos

Los cupos disponibles se calculan contando inscripciones con:

```text
status = active
```

Si el curso tiene `max_students = 0`, se considera inscripcion abierta.

Si una inscripcion se cancela, al eliminarse el registro el cupo vuelve a quedar disponible.

## Auth / Seguridad

El login actual funciona con Auth0.

Credenciales/config actual en `.env` y `frontend/.env`:

- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_AUDIENCE`
- `OIDC_ISSUER`
- `OIDC_CLIENT_ID`
- `OIDC_AUDIENCE`
- `OIDC_ALGORITHMS=RS256`

El backend fue abstraido a OIDC generico:

- `backend/app/core/oidc.py`
- `backend/app/core/auth0.py` queda como wrapper compatible
- `backend/app/core/admin_auth.py` usa claims OIDC para resolver usuario

Esto permite que en el futuro se pueda migrar a Okta o Entra ID cambiando configuracion del proveedor.

Importante:

- El frontend todavia usa `@auth0/auth0-vue`, por lo tanto Auth0 sigue siendo el adapter real del login.
- Para soportar Okta/Entra completamente en frontend, conviene migrar a un cliente OIDC generico como `oidc-client-ts`.

## Roles

Roles esperados:

- Usuario normal: puede ver cursos, crear su perfil de suscriptor, suscribirse y cancelar sus propias suscripciones.
- Administrador: puede gestionar cursos, usuarios, suscriptores, inscripciones y pagos manuales.

El admin inicial definido fue:

```text
admin@example.com
```

Las rutas admin estan protegidas en backend con `require_admin`.

El router frontend tambien redirige fuera de `/admin` si `localStorage.app_user.is_admin` no es verdadero. Esto es solo UX; la seguridad real esta en backend.

## UI / Navegacion

Se diferencio el nombre del sector admin de cursos:

- User front: `Courses`
- Admin: `Course Admin`

La vista admin muestra:

- metricas de cursos
- cursos publicados
- suscripciones activas
- cupos disponibles
- capacidad total
- tabla `Managed courses`
- detalle de suscriptores por curso

El backoffice generico anterior fue removido del flujo:

- `/admin` redirige a `/admin/courses`
- nav admin muestra `Users` y `Course Admin`

## Assets

Assets relevantes:

- `frontend/src/assets/logos/labschool_nav_mark.png`
- `frontend/src/assets/banners/header_main_clean.png`

El logo del nav fue creado/ajustado para encajar con el fondo oscuro del navbar.

## Publicacion En OpenMediaVault

Plan recomendado:

- copiar el proyecto al server OMV
- usar Docker Compose
- usar SQL Server con volumen persistente o base externa
- publicar via nginx o Nginx Proxy Manager
- usar HTTPS con Let's Encrypt

Para produccion conviene:

- no exponer frontend directo salvo que sea necesario
- publicar nginx del proyecto o apuntar Nginx Proxy Manager al puerto interno elegido
- configurar Auth0 con el dominio final:
  - Allowed Callback URLs
  - Allowed Logout URLs
  - Allowed Web Origins
  - Allowed Origins CORS

## Problemas Recurrentes

### 502 Bad Gateway

Causa vista:

- nginx cachea la IP vieja del contenedor `frontend`
- luego de recrear `frontend`, nginx sigue intentando ir a la IP anterior

Solucion:

```bash
docker compose restart nginx
```

### Puertos Directos

Puertos host definidos:

- API: `8400:8000`
- Frontend: `8401:3000`

## Estado Git

Repositorio Git operativo en branch `develop`.

Remoto esperado:

```bash
git remote -v
```

debe apuntar a:

```text
https://github.com/gerh87/ph.lab.subscription.portal.git
```

## Pagos

Flujo hibrido definido:

- Cursos gratis: la inscripcion queda `active` y `payment_status=paid`.
- Cursos pagos con transferencia/manual: la inscripcion queda `pending_payment` y `payment_status=pending`; un admin la confirma desde Course Admin.
- Cursos pagos con Mercado Pago: la inscripcion queda `pending_payment`; se crea una preference y el webhook cambia a `active/paid` cuando Mercado Pago informa pago aprobado.

Campos agregados en `enrollments`:

- `payment_method`: `free`, `manual` o `mercadopago`.
- `payment_reference`: referencia manual o id de pago.
- `payment_provider_id`: id de preference/pago del proveedor.
- `payment_provider_status`: estado informado por el proveedor.
- `manual_payment_notes`: notas internas de aprobacion manual.
- `payment_requested_at`: fecha de inicio del intento de pago.
- `paid_at`: fecha de confirmacion de pago.

Endpoints relevantes:

- `POST /api/v1/payments/create_preference`
- `POST /api/v1/payments/webhook/mp`
- `POST /api/v1/enrollments/{id}/pay`

Variables Mercado Pago:

- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_NOTIFICATION_URL`
- `MERCADOPAGO_WEBHOOK_SECRET` opcional pero recomendado para validar la firma del webhook.

Pendiente de produccion:

- probar sandbox completo con usuario comprador de prueba
- configurar `MERCADOPAGO_WEBHOOK_SECRET`
- cambiar a credenciales productivas cuando el ambiente deje de ser prueba

## Pendientes Sugeridos

- Separar compose local y compose prod, por ejemplo `docker-compose.prod.yml`.
- Migrar frontend a OIDC generico si se quiere soportar Okta/Entra sin reescribir login.
- Revisar si `zoom_url` debe ser visible solo para admin y no en respuestas publicas.
- Agregar tests de seguridad para:
  - usuario normal no accede admin
  - usuario normal no obtiene Zoom de inscripcion ajena
  - Zoom solo disponible el dia del curso
  - pago manual solo lo confirma admin
  - webhook Mercado Pago marca pago aprobado
- Decidir si se necesitan pagos rechazados/anulados con historial separado.
- Decidir si se necesita historial/auditoria de bajas en el futuro.
