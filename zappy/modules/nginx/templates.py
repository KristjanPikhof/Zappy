"""Nginx configuration templates."""

from typing import Dict, Optional
from ...config import NGINX_LOG_DIR

# Available template types
TEMPLATE_TYPES = {
    "proxy": "Reverse Proxy (default)",
    "proxy-ws": "Reverse Proxy with WebSocket support",
    "static": "Static file serving",
    "php": "PHP application (php-fpm)",
    "redirect": "HTTP redirect",
}


def get_template(
    template_type: str,
    server_name: str,
    proxy_pass: Optional[str] = None,
    root_path: Optional[str] = None,
    redirect_url: Optional[str] = None,
    php_socket: str = "/run/php/php-fpm.sock",
) -> str:
    """Generate an nginx configuration from a template.

    Args:
        template_type: Type of template (proxy, proxy-ws, static, php, redirect)
        server_name: Domain name
        proxy_pass: Backend URL for proxy templates
        root_path: Root path for static/php templates
        redirect_url: Target URL for redirect template
        php_socket: PHP-FPM socket path

    Returns:
        Nginx configuration string
    """
    templates = {
        "proxy": _template_proxy,
        "proxy-ws": _template_proxy_websocket,
        "static": _template_static,
        "php": _template_php,
        "redirect": _template_redirect,
    }

    generator = templates.get(template_type, _template_proxy)
    return generator(
        server_name=server_name,
        proxy_pass=proxy_pass,
        root_path=root_path,
        redirect_url=redirect_url,
        php_socket=php_socket,
    )


def _template_proxy(
    server_name: str,
    proxy_pass: Optional[str] = None,
    **kwargs,
) -> str:
    """Standard reverse proxy template."""
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    location / {{
        proxy_pass {proxy_pass};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    error_log {NGINX_LOG_DIR}/{server_name}_error.log;
    access_log {NGINX_LOG_DIR}/{server_name}_access.log;
}}
"""


def _template_proxy_websocket(
    server_name: str,
    proxy_pass: Optional[str] = None,
    **kwargs,
) -> str:
    """Reverse proxy template with WebSocket support."""
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    location / {{
        proxy_pass {proxy_pass};
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
    }}

    error_log {NGINX_LOG_DIR}/{server_name}_error.log;
    access_log {NGINX_LOG_DIR}/{server_name}_access.log;
}}
"""


def _template_static(
    server_name: str,
    root_path: Optional[str] = None,
    **kwargs,
) -> str:
    """Static file serving template."""
    root = root_path or f"/var/www/{server_name}"
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    root {root};
    index index.html index.htm;

    location / {{
        try_files $uri $uri/ =404;
    }}

    # Cache static assets
    location ~* \\.(jpg|jpeg|png|gif|ico|css|js|woff2?)$ {{
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    error_log {NGINX_LOG_DIR}/{server_name}_error.log;
    access_log {NGINX_LOG_DIR}/{server_name}_access.log;
}}
"""


def _template_php(
    server_name: str,
    root_path: Optional[str] = None,
    php_socket: str = "/run/php/php-fpm.sock",
    **kwargs,
) -> str:
    """PHP application template with php-fpm."""
    root = root_path or f"/var/www/{server_name}"
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    root {root};
    index index.php index.html index.htm;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    location ~ \\.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:{php_socket};
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }}

    # Deny access to hidden files
    location ~ /\\. {{
        deny all;
    }}

    error_log {NGINX_LOG_DIR}/{server_name}_error.log;
    access_log {NGINX_LOG_DIR}/{server_name}_access.log;
}}
"""


def _template_redirect(
    server_name: str,
    redirect_url: Optional[str] = None,
    **kwargs,
) -> str:
    """HTTP redirect template."""
    target = redirect_url or f"https://{server_name}"
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    return 301 {target}$request_uri;

    error_log {NGINX_LOG_DIR}/{server_name}_error.log;
    access_log {NGINX_LOG_DIR}/{server_name}_access.log;
}}
"""
