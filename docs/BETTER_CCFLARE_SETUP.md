# Better-CCFlare Setup Guide

Deploy [better-ccflare](https://github.com/tombii/better-ccflare) securely using Zappy with nginx reverse proxy and IP restriction.

---

## Prerequisites

- Zappy installed (`zappy` command available)
- Docker installed (use `zappy` → Docker Setup → Install Docker)
- A domain pointing to your server
- Your public IP address (run `curl ifconfig.me`)

---

## Step 1: Create Docker Compose File

Create the stack directory:

```bash
sudo mkdir -p /opt/stacks/better-ccflare
cd /opt/stacks/better-ccflare
```

Create `compose.yaml`:

```bash
sudo nano compose.yaml
```

Paste this configuration:

```yaml
services:
  better-ccflare:
    image: ghcr.io/tombii/better-ccflare:latest
    container_name: better-ccflare
    restart: unless-stopped
    ports:
      - 127.0.0.1:8080:8080  # localhost only - nginx proxies to it
    volumes:
      - better-ccflare-data:/data
    environment:
      - NODE_ENV=production
      - BETTER_CCFLARE_DB_PATH=/data/better-ccflare.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  better-ccflare-data:
    driver: local
```

> **Note:** We bind to `127.0.0.1:8080` so the app is only accessible via nginx, not directly from the internet.

---

## Step 2: Create Nginx Configuration

Run Zappy:

```bash
zappy
```

Navigate to:
```
Nginx Management → Add domain
```

1. Enter your domain (e.g., `ccflare.example.com`)
2. Select **Reverse Proxy with WebSocket support**
3. Enter backend URL: `8080`

---

## Step 3: Add IP Restriction (Optional but Recommended)

Edit the nginx config using Zappy:

```bash
zappy
# Nginx Management → View/Edit config → Select your domain
```

Or manually:
```bash
sudo nano /etc/nginx/sites-available/ccflare.example.com
```

Add the `allow`/`deny` directives right after `server_name`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name ccflare.example.com;

    # IP Restriction - only allow your IP
    allow YOUR.PUBLIC.IP.HERE;
    deny all;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for WebSocket
        proxy_connect_timeout 60s;
        proxy_send_timeout 86400s;
        proxy_read_timeout 86400s;
    }

    error_log /var/log/nginx/ccflare.example.com_error.log;
    access_log /var/log/nginx/ccflare.example.com_access.log;
}
```

**Find your public IP:**
```bash
curl ifconfig.me
```

**Multiple IPs:** Add multiple `allow` lines:
```nginx
allow 1.2.3.4;
allow 5.6.7.8;
deny all;
```

**Optional - Redirect blocked users:** Instead of showing a 403 Forbidden page, redirect unauthorized visitors to another site:

```nginx
# IP Restriction
allow YOUR.PUBLIC.IP.HERE;
deny all;

# Redirect 403 (blocked) to your main site
error_page 403 = @denied;
location @denied {
    return 302 https://your-main-site.com;
}
```

This way, anyone not on your IP allowlist gets silently redirected instead of seeing an error page.

---

## Step 4: Enable the Site

If you created the domain via Zappy, it will ask if you want to enable it automatically.

To enable manually:
```bash
zappy
# Nginx Management → Enable domain → Select your domain
```

Or via command line:
```bash
sudo nginx -t
sudo ln -sf /etc/nginx/sites-available/ccflare.example.com /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

---

## Step 5: Add SSL Certificate

Make sure ports 80 and 443 are open:

```bash
zappy
# Firewall Management → Allow service → HTTP
# Firewall Management → Allow service → HTTPS
```

Then add HTTPS:

```bash
zappy
# Nginx Management → SSL Certificates → Add HTTPS to domain
# Select your domain
# Enter email for notifications
```

---

## Step 6: Start the Container

```bash
cd /opt/stacks/better-ccflare
sudo docker compose up -d
```

Check status:
```bash
sudo docker compose ps
sudo docker compose logs -f
```

---

## Step 7: Access Better-CCFlare

Open in your browser:
```
https://ccflare.example.com
```

If you set up IP restriction, only your IP can access it. Others will see **403 Forbidden**.

---

## Managing the Stack

**View logs:**
```bash
cd /opt/stacks/better-ccflare
sudo docker compose logs -f
```

**Restart:**
```bash
sudo docker compose restart
```

**Stop:**
```bash
sudo docker compose down
```

**Update to latest version:**
```bash
sudo docker compose pull
sudo docker compose up -d
```

---

## Using Dockge (Optional)

If you installed Dockge via Zappy, you can manage this stack through the web UI:

1. Open Dockge at `http://your-server:5001`
2. Click "Add Stack"
3. Name it `better-ccflare`
4. Paste the compose.yaml content
5. Deploy

---

## Troubleshooting

### 502 Bad Gateway
Container not running or wrong port:
```bash
sudo docker compose ps
sudo docker compose logs
```

### 504 Gateway Timeout
Check proxy_pass has correct format:
```nginx
proxy_pass http://127.0.0.1:8080;  # Correct
proxy_pass http://8080;             # Wrong!
```

### 403 Forbidden
Your IP is not in the allow list. Check your current IP:
```bash
curl ifconfig.me
```

Update nginx config with your IP and reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Connection Refused
Make sure container is binding to the right interface:
```bash
sudo docker compose ps
# Should show 127.0.0.1:8080->8080/tcp
```

---

## Security Notes

- **IP Restriction:** Highly recommended for admin panels
- **Localhost Binding:** The `127.0.0.1:8080` binding ensures the app is never directly exposed
- **SSL:** Always use HTTPS in production
- **Firewall:** Only ports 22, 80, and 443 should be open to the public
