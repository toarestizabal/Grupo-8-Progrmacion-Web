# PixelForge Games

Proyecto grupal de Programación Web. Es una tienda de videojuegos desarrollada con Django y Oracle 19c.

La aplicación permite registrar clientes, iniciar sesión, recuperar la contraseña, modificar el perfil, comprar mediante un carrito y revisar pedidos. El administrador puede gestionar productos, inventario, usuarios y estados de pedidos. El pago es solamente una simulación.

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

## Cuentas para probar

- Administrador: `admin` / `Admin123!`
- Cliente: `cliente` / `Cliente123!`

## Archivos de Oracle

Dentro de la carpeta `database` están:

- `create_user.sql`: crea el usuario de Oracle que usa la aplicación.
- `schema.sql`: contiene la estructura de las tablas solicitada para la entrega.
- `seed.sql`: contiene los datos iniciales en SQL.
- `MER_PixelForge.png`: diagrama de la base de datos.

El modelo contiene 9 tablas funcionales y está normalizado hasta tercera forma normal.

Normalmente las tablas se crean con `python manage.py migrate`. No hay que ejecutar `schema.sql` encima de una base que ya fue migrada, porque intenta crear las mismas tablas.

Para confirmar que Django está conectado a Oracle se puede usar:

```powershell
python manage.py verify_oracle
```

