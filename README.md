# PixelForge Games

Es una tienda de videojuegos desarrollada con Django y Oracle 19c.

La aplicación permite registrar clientes, iniciar sesión, recuperar la contraseña, modificar el perfil, comprar mediante un carrito y revisar pedidos. El administrador puede gestionar productos, inventario, usuarios y estados de pedidos. El pago es solamente una simulación.

También incluye dos API REST propias, una para categorías y otra para productos. La tienda consulta servicios públicos para mostrar recomendaciones, información de cada producto y sus tráileres sin recargar la página.

Repositorio: https://github.com/toarestizabal/Grupo-8-Progrmacion-Web

## Requisitos

- Python 3.10 o superior.
- Oracle Database 19c con la base `ORCLPDB` disponible.



## Cómo ejecutar el proyecto

Primero se crea y activa el entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Después hay que crear el usuario de Oracle. Desde SQL*Plus, conectado como `SYSDBA`:

```sql
@database/create_user.sql
```

El script pedirá la contraseña que tendrá el usuario `PIXELFORGE_APP`.

Luego se copia `.env.example` como `.env`:

```powershell
Copy-Item .env.example .env
```

En `.env` se debe cambiar `ORACLE_PASSWORD` por la misma contraseña usada al crear `PIXELFORGE_APP`. También se debe reemplazar `DJANGO_SECRET_KEY` por una clave larga.

Con Oracle listo, se crean las tablas y se cargan los datos de ejemplo:

```powershell
python manage.py migrate
python manage.py seed_data --reset-passwords
python manage.py runserver
```

La tienda queda disponible en http://127.0.0.1:8000/

## API REST

La API usa autenticación por token. Para obtener uno se envían `username` y `password` mediante `POST`:

```text
http://127.0.0.1:8000/api/token/
```

Por ejemplo, el cuerpo JSON para una cuenta administradora es:

```json
{
  "username": "admin",
  "password": "Admin123!"
}
```

La respuesta contiene el token y su fecha de vencimiento en `expira_en`. Cada token dura 24 horas; el plazo puede cambiarse con `API_TOKEN_TTL_HOURS` en `.env`. Si vence, se repite la misma solicitud y se recibe uno nuevo. Solicitar un token nuevo invalida el anterior.

El CRUD de categorías está en:

```text
http://127.0.0.1:8000/api/categorias/
```

El CRUD de productos está en:

```text
http://127.0.0.1:8000/api/productos/
```

Ambas API admiten `GET`, `POST`, `PUT`, `PATCH` y `DELETE`. Todos los accesos requieren token; los clientes pueden consultar y solamente los administradores pueden modificar. Categorías permite filtrar con `?activa=true` y `?buscar=texto`. Productos permite usar `?activo=true`, `?categoria=slug`, `?en_stock=true` y `?buscar=texto`.

En las solicitudes se usa la cabecera `Authorization: Token <token>`. En un despliegue real esta autenticación debe utilizarse mediante HTTPS.

Para revocar el token antes de su vencimiento se envía un `POST` a:

```text
http://127.0.0.1:8000/api/token/revocar/
```

Esta solicitud también debe incluir la cabecera `Authorization: Token <token>`. El procedimiento puede realizarse desde Postman sin modificar el código del proyecto.

La página `http://127.0.0.1:8000/explorar-juegos/` consume FreeToGame mediante JavaScript. Además, el botón **Ver detalles** de cada producto abre una ficha interna que combina información de Steam Store o Wikidata con un tráiler consultado mediante YouTube oEmbed. Los diez productos tienen la misma ficha y no se necesitan claves ni cuentas para utilizar estos servicios.

## Cuentas para probar

- Administrador: `admin` / `Admin123!`
- Cliente: `cliente` / `Cliente123!`

## Archivos de Oracle

Dentro de la carpeta `database` están:

- `create_user.sql`: crea el usuario de Oracle que usa la aplicación.
- `create_test_user.sql`: crea el esquema aislado para las pruebas automatizadas.
- `schema.sql`: contiene la estructura de las tablas solicitada para la entrega.
- `seed.sql`: contiene los datos iniciales en SQL.
- `MER_PixelForge.png`: diagrama de la base de datos.

El modelo contiene 9 tablas funcionales y está normalizado hasta tercera forma normal.

Normalmente las tablas se crean con `python manage.py migrate`. No hay que ejecutar `schema.sql` encima de una base que ya fue migrada, porque intenta crear las mismas tablas.

Para confirmar que Django está conectado a Oracle se puede usar:

```powershell
python manage.py verify_oracle
```

## Pruebas automatizadas

Las pruebas usan el esquema aislado `PIXELFORGE_TEST`; nunca crean, borran ni
modifican tablas de `PIXELFORGE_APP`. Se prepara una sola vez desde SQL*Plus,
conectado como `SYSDBA`:

```sql
@database/create_test_user.sql
```

La contraseña elegida se configura en `.env` como `ORACLE_TEST_PASSWORD`.
Después, la suite completa se ejecuta conservando ese esquema de pruebas:

```powershell
python manage.py test --keepdb
```

## Configuración para despliegue

En el servidor se deben definir `DJANGO_PRODUCTION=True`, `DJANGO_DEBUG=False`,
una `DJANGO_SECRET_KEY` aleatoria de al menos 50 caracteres, el dominio en
`DJANGO_ALLOWED_HOSTS` y su URL HTTPS en `DJANGO_CSRF_TRUSTED_ORIGINS`. Con ese
modo activo, Django exige HTTPS y habilita cookies seguras y HSTS. El entorno
local mantiene HTTP para facilitar el desarrollo.

