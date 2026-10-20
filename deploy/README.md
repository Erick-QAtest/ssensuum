# Despliegue en el VPS

VPS Contabo `vmi3626066` (`167.86.94.254`, Ubuntu 24.04), compartido con lexradar y
sportland-smart. Sigue la misma convención que esos sitios: servicios systemd detrás de
nginx, con HTTPS de certbot.

| Pieza | Dónde |
|---|---|
| Código | `/opt/ssensuum` (usuario de sistema `ssensuum`) |
| Base de datos | `/opt/ssensuum/data/ssensuum.db` |
| API | `ssensuum-api.service` → `127.0.0.1:8100` |
| Web | `ssensuum-web.service` → `127.0.0.1:3100` |
| nginx | `/etc/nginx/sites-available/ssensuum` |
| Usuario admin | `/etc/nginx/ssensuum.htpasswd` |
| Credenciales de Mercado Pago | `/etc/ssensuum/api.env` (solo root) |

Rutas públicas:

- `https://ssensuum.mx/` → web
- `https://ssensuum.mx/api/*` → API (sin el prefijo `/api`)
- `https://www.ssensuum.mx` → redirige a `https://ssensuum.mx`
- `/admin*`, `/api/customers*` y `/api/admin/*` piden usuario y contraseña
- `/api/docs` está bloqueado

## Desplegar o actualizar

Desde la raíz del repo, en la Mac:

```bash
rsync -az --delete --exclude .git --exclude node_modules --exclude .next --exclude .venv --exclude '*.db' --exclude .pytest_cache --exclude __pycache__ --exclude .env --exclude .env.local --exclude api/storage ./ lexradar@167.86.94.254:ssensuum-src/
```

```bash
ssh -t lexradar@167.86.94.254 sudo bash ssensuum-src/deploy/vps-deploy.sh
```

La primera vez pide el usuario y la contraseña admin, y certbot emite el certificado.
Las siguientes veces solo actualiza código, dependencias y reinicia los servicios.

## Operación

```bash
sudo systemctl status ssensuum-api ssensuum-web
sudo journalctl -u ssensuum-api -n 100
```

Activar o cambiar las credenciales de Mercado Pago (sin token, el sitio confirma por WhatsApp).
Con credenciales de prueba agrega también `MP_SANDBOX=true`; quítalo al poner las productivas:

```bash
sudo nano /etc/ssensuum/api.env
sudo systemctl restart ssensuum-api
```

Cambiar la contraseña admin:

```bash
sudo rm /etc/nginx/ssensuum.htpasswd && sudo bash ~/ssensuum-src/deploy/vps-deploy.sh
```

Respaldo de la base de datos:

```bash
sudo -u ssensuum sqlite3 /opt/ssensuum/data/ssensuum.db ".backup /opt/ssensuum/data/backup-$(date +%F).db"
```
