"""Global configuration for Zappy the VPS Toolbox."""

import os
from pathlib import Path
from datetime import datetime

# Nginx paths
NGINX_SITES_AVAILABLE = "/etc/nginx/sites-available"
NGINX_SITES_ENABLED = "/etc/nginx/sites-enabled"
NGINX_LOG_DIR = "/var/log/nginx"

# Backup directory
BACKUP_DIR = Path("/var/backups/zappy")

# Docker paths
DOCKGE_DIR = Path("/opt/dockge")
DOCKER_STACKS_DIR = Path("/opt/stacks")

# AiTermy path
AITERMY_DIR = Path("/opt/aitermy")

# SSH config
SSH_CONFIG_PATH = Path("/etc/ssh/sshd_config")

# Certbot
CERTBOT_EMAIL_FILE = Path.home() / ".zappy" / "certbot-email"


def get_backup_path(config_type: str, name: str = "") -> Path:
    """Generate a timestamped backup path.

    Args:
        config_type: Type of config (nginx, ssh, etc.)
        name: Optional name identifier

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{config_type}_{name}_{timestamp}.bak" if name else f"{config_type}_{timestamp}.bak"
    return BACKUP_DIR / config_type / filename


def ensure_backup_dir(config_type: str) -> Path:
    """Ensure backup directory exists.

    Args:
        config_type: Type of config (nginx, ssh, etc.)

    Returns:
        Path to backup directory
    """
    backup_path = BACKUP_DIR / config_type
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path
