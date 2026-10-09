#!/usr/bin/env bash
set -Eeuo pipefail

DOMAIN="${1:?Uso: azure_provision.sh dominio-publico}"
REPOSITORY="https://github.com/toarestizabal/Grupo-8-Progrmacion-Web.git"
APP_DIR="/opt/pixelforge"
SECRETS_FILE="/root/pixelforge-secrets.env"
ORACLE_RPM="/var/tmp/oracle-database-free-23ai-1.0-1.el9.x86_64.rpm"
ORACLE_RPM_URL="https://download.oracle.com/otn-pub/otn_software/db-free/oracle-database-free-23ai-1.0-1.el9.x86_64.rpm"

if [[ $EUID -ne 0 ]]; then
    echo "Este script debe ejecutarse como root." >&2
    exit 1
fi

echo "[1/9] Preparando sistema"
if ! swapon --show | grep -q .; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

dnf install -y \
    oracle-database-preinstall-23ai \
    python3.11 python3.11-pip python3.11-devel \
    git nginx curl gcc policycoreutils-python-utils

echo "[2/9] Instalando Oracle Database Free"
if ! rpm -q oracle-database-free-23ai >/dev/null 2>&1; then
    curl --fail --location --retry 3 --output "$ORACLE_RPM" "$ORACLE_RPM_URL"
    dnf install -y "$ORACLE_RPM"
fi

if [[ ! -f "$SECRETS_FILE" ]]; then
    umask 077
    {
        echo "ORACLE_SYS_PASSWORD=Ora_$(openssl rand -hex 16)"
        echo "ORACLE_SCHEMA_PASSWORD=Pf_$(openssl rand -hex 16)"
        echo "DJANGO_SECRET_KEY=$(openssl rand -hex 48)"
    } > "$SECRETS_FILE"
fi
# shellcheck disable=SC1090
source "$SECRETS_FILE"

if [[ ! -d /opt/oracle/oradata/FREE ]]; then
    printf '%s\n%s\n' "$ORACLE_SYS_PASSWORD" "$ORACLE_SYS_PASSWORD" \
        | /etc/init.d/oracle-free-23ai configure
fi
systemctl enable --now oracle-free-23ai

echo "[3/9] Creando esquema de la aplicacion"
export ORACLE_HOME=/opt/oracle/product/23ai/dbhomeFree
export ORACLE_SID=FREE
export PATH="$ORACLE_HOME/bin:$PATH"
runuser -u oracle -- "$ORACLE_HOME/bin/sqlplus" -s '/ as sysdba' <<SQL
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM dba_users WHERE username = 'PIXELFORGE_APP';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE USER PIXELFORGE_APP IDENTIFIED BY "$ORACLE_SCHEMA_PASSWORD"';
    ELSE
        EXECUTE IMMEDIATE 'ALTER USER PIXELFORGE_APP IDENTIFIED BY "$ORACLE_SCHEMA_PASSWORD" ACCOUNT UNLOCK';
    END IF;
END;
/
ALTER USER PIXELFORGE_APP QUOTA UNLIMITED ON USERS;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE TRIGGER,
      CREATE VIEW, CREATE PROCEDURE TO PIXELFORGE_APP;
EXIT
SQL

echo "[4/9] Descargando PixelForge"
if [[ -d "$APP_DIR/.git" ]]; then
    git -C "$APP_DIR" fetch origin main
    git -C "$APP_DIR" reset --hard origin/main
else
    rm -rf "$APP_DIR"
    git clone --branch main --single-branch "$REPOSITORY" "$APP_DIR"
fi
id pixelforge >/dev/null 2>&1 || useradd --system --home-dir "$APP_DIR" --shell /sbin/nologin pixelforge

echo "[5/9] Instalando dependencias de Python"
python3.11 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" gunicorn

cat > "$APP_DIR/.env" <<ENV
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_PRODUCTION=True
DJANGO_ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMAIN
DJANGO_SECURE_HSTS_SECONDS=3600
API_TOKEN_TTL_HOURS=24
ORACLE_DSN=localhost:1521/FREEPDB1
ORACLE_USER=PIXELFORGE_APP
ORACLE_PASSWORD=$ORACLE_SCHEMA_PASSWORD
SEED_ADMIN_PASSWORD=Admin123!
SEED_CLIENT_PASSWORD=Cliente123!
ENV
chown -R pixelforge:pixelforge "$APP_DIR"
chmod 600 "$APP_DIR/.env"

echo "[6/9] Creando tablas y datos iniciales"
cd "$APP_DIR"
sudo -u pixelforge "$APP_DIR/.venv/bin/python" manage.py migrate --noinput
sudo -u pixelforge "$APP_DIR/.venv/bin/python" manage.py seed_data --reset-passwords
sudo -u pixelforge "$APP_DIR/.venv/bin/python" manage.py collectstatic --noinput

echo "[7/9] Configurando Gunicorn"
cat > /etc/systemd/system/pixelforge.service <<UNIT
[Unit]
Description=PixelForge Django con Gunicorn
After=network.target oracle-free-23ai.service
Requires=oracle-free-23ai.service

[Service]
User=pixelforge
Group=pixelforge
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
ExecStart=$APP_DIR/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 pixelforge.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now pixelforge

echo "[8/9] Configurando Nginx y HTTPS"
cat > /etc/nginx/conf.d/pixelforge.conf <<NGINX
server {
    listen 80;
    server_name $DOMAIN;

    location /static/ {
        alias $APP_DIR/staticfiles/;
    }

    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINX
semanage fcontext -a -t httpd_sys_content_t "$APP_DIR/staticfiles(/.*)?" 2>/dev/null || \
    semanage fcontext -m -t httpd_sys_content_t "$APP_DIR/staticfiles(/.*)?"
restorecon -RF "$APP_DIR/staticfiles"
setsebool -P httpd_can_network_connect 1

# Los dominios regionales de Azure superan el tamaño predeterminado de Nginx.
if ! grep -qE '^[[:space:]]*server_names_hash_bucket_size' /etc/nginx/nginx.conf; then
    sed -i '/^http {/a\    server_names_hash_bucket_size 128;' /etc/nginx/nginx.conf
fi
nginx -t
systemctl enable --now nginx

if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
fi

dnf install -y oracle-epel-release-el9
dnf install -y certbot python3-certbot-nginx
certbot --nginx --non-interactive --agree-tos --register-unsafely-without-email \
    --redirect --domain "$DOMAIN"
systemctl enable --now certbot-renew.timer

echo "[9/9] Verificando despliegue"
systemctl restart pixelforge nginx
sudo -u pixelforge "$APP_DIR/.venv/bin/python" manage.py check --deploy
curl --fail --silent --show-error --location "https://$DOMAIN/" >/dev/null
echo "PixelForge disponible en https://$DOMAIN/"
