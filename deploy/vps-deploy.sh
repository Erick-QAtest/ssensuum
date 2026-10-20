#!/usr/bin/env bash
# Instala o actualiza SSENSUUM en el VPS (Ubuntu 24.04 con nginx + certbot).
# Uso, desde el VPS:  sudo bash ~/ssensuum-src/deploy/vps-deploy.sh
# Es seguro correrlo varias veces: la base de datos, la contraseña admin y la
# configuración de nginx/HTTPS existentes se conservan.
set -euo pipefail

DOMAIN=ssensuum.mx
APP=/opt/ssensuum
API_PORT=8100
WEB_PORT=3100
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HTPASSWD=/etc/nginx/ssensuum.htpasswd
SITE=/etc/nginx/sites-available/ssensuum
SECRETS=/etc/ssensuum/api.env

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta con sudo."; exit 1; }

echo "==> Node.js"
command -v npm >/dev/null || { apt-get update -q; apt-get install -y -q nodejs npm; }

echo "==> Usuario de sistema"
id ssensuum >/dev/null 2>&1 || useradd --system --home-dir "$APP" --shell /usr/sbin/nologin ssensuum

echo "==> Código en $APP"
mkdir -p "$APP/data"
rsync -a --delete \
  --exclude /data --exclude /.npm --exclude /api/.venv \
  --exclude /web/node_modules --exclude /web/.next \
  --exclude .git --exclude '*.db' --exclude .env --exclude .env.local \
  "$SRC/" "$APP/"
chown -R ssensuum:ssensuum "$APP"
chmod 750 "$APP"

echo "==> Dependencias y build"
sudo -u ssensuum -H bash -euo pipefail -c "
  export npm_config_cache='$APP/.npm' NEXT_TELEMETRY_DISABLED=1
  cd '$APP/api'
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
  cd '$APP/web'
  npm ci --no-audit --no-fund
  NEXT_PUBLIC_API_BASE_URL=/api npm run build
"

echo "==> Secretos de la API"
if [ ! -f "$SECRETS" ]; then
  mkdir -p /etc/ssensuum
  printf '%s\n' "# Access token de Mercado Pago: el de prueba mientras se valida, el productivo para cobrar de verdad." "MP_ACCESS_TOKEN=" > "$SECRETS"
  chmod 600 "$SECRETS"
  echo "Creado $SECRETS (pagos desactivados hasta poner MP_ACCESS_TOKEN)."
fi

echo "==> Servicios systemd"
cat > /etc/systemd/system/ssensuum-api.service <<EOF
[Unit]
Description=SSENSUUM API
After=network.target

[Service]
User=ssensuum
Group=ssensuum
WorkingDirectory=$APP/api
Environment=DATABASE_URL=sqlite:///$APP/data/ssensuum.db
Environment=HR_FILES_DIR=$APP/data/rh
Environment=WEB_ORIGIN=https://$DOMAIN
Environment=PUBLIC_BASE_URL=https://$DOMAIN
EnvironmentFile=$SECRETS
# Un solo worker: la prevención de doble reserva del MVP vive en memoria del proceso.
ExecStart=$APP/api/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $API_PORT --workers 1 --proxy-headers
Restart=on-failure
RestartSec=4
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/ssensuum-web.service <<EOF
[Unit]
Description=SSENSUUM Web
After=network.target ssensuum-api.service

[Service]
User=ssensuum
Group=ssensuum
WorkingDirectory=$APP/web
Environment=NODE_ENV=production
Environment=NEXT_TELEMETRY_DISABLED=1
ExecStart=$APP/web/node_modules/.bin/next start -p $WEB_PORT -H 127.0.0.1
Restart=on-failure
RestartSec=4
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable -q ssensuum-api ssensuum-web
systemctl restart ssensuum-api ssensuum-web

echo "==> Usuario admin (protege /admin y los datos de clientes)"
if [ ! -f "$HTPASSWD" ]; then
  read -rp "Usuario admin: " admin_user
  read -rsp "Contraseña admin: " admin_pass; echo
  printf '%s:%s\n' "$admin_user" "$(openssl passwd -apr1 "$admin_pass")" > "$HTPASSWD"
  chown root:www-data "$HTPASSWD"
  chmod 640 "$HTPASSWD"
else
  echo "Ya existe $HTPASSWD, se conserva."
fi

echo "==> nginx"
if [ ! -f "$SITE" ]; then
  cat > "$SITE" <<EOF
server {
    server_name $DOMAIN www.$DOMAIN;

    if (\$host = www.$DOMAIN) {
        return 301 https://$DOMAIN\$request_uri;
    }

    client_max_body_size 10m;

    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 60s;

    # La API aún no tiene autenticación: lo administrativo y los datos de clientes
    # quedan detrás de usuario y contraseña.
    location /admin {
        auth_basic "SSENSUUM admin";
        auth_basic_user_file $HTPASSWD;
        proxy_pass http://127.0.0.1:$WEB_PORT;
    }

    location /api/customers {
        auth_basic "SSENSUUM admin";
        auth_basic_user_file $HTPASSWD;
        proxy_pass http://127.0.0.1:$API_PORT/customers;
    }

    location /api/admin/ {
        auth_basic "SSENSUUM admin";
        auth_basic_user_file $HTPASSWD;
        proxy_pass http://127.0.0.1:$API_PORT/admin/;
    }

    location ~ ^/api/(docs|redoc|openapi\.json) {
        return 404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:$API_PORT/;
    }

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
    }

    listen 80;
    listen [::]:80;
}
EOF
  ln -sf "$SITE" /etc/nginx/sites-enabled/ssensuum
else
  echo "Ya existe $SITE, se conserva."
fi
nginx -t
systemctl reload nginx

echo "==> HTTPS"
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --redirect
else
  echo "Certificado ya existe."
fi

echo "==> Verificación"
# La API tarda unos segundos en arrancar: se reintenta hasta 30 s antes de dar error.
for _ in $(seq 30); do
  curl -fsS "http://127.0.0.1:$API_PORT/health" 2>/dev/null && echo && break
  sleep 1
done || true
curl -fsS "http://127.0.0.1:$API_PORT/health" >/dev/null || echo "La API no respondió en 30 s: revisa journalctl -u ssensuum-api"
curl -fsS -o /dev/null -w "web: HTTP %{http_code}\n" "http://127.0.0.1:$WEB_PORT/"
echo
echo "Listo: https://$DOMAIN"
