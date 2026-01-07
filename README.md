# Zappy the VPS Toolbox

A comprehensive VPS management CLI tool for Linux servers.

---

## 🚀 New VPS? Start Here!

**[📖 New VPS Setup Guide](docs/NEW_VPS_SETUP.md)** - Complete step-by-step guide to securely set up a brand new VPS from scratch.

---

## Features

- **Nginx Management**: Add, enable, disable, delete domain configurations with multiple templates (reverse proxy, WebSocket, static, PHP)
- **SSL Certificates**: Automated Certbot integration for HTTPS
- **Firewall Management**: UFW and firewalld support for port/service management
- **Security Hardening**: SSH configuration, fail2ban setup, automatic security updates
- **Docker Setup**: Install Docker and Dockge (Docker Compose manager)
- **System Utilities**: Common tools installation, zsh + oh-my-zsh setup, AiTermy, system monitoring

## Supported Distributions

- Debian / Ubuntu
- RHEL / CentOS / Fedora / Rocky / Alma
- Arch Linux
- Alpine Linux
- openSUSE

## Installation

### Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/KristjanPikhof/Zappy/main/install.sh | sudo bash
```

Or with git clone:

```bash
git clone https://github.com/KristjanPikhof/Zappy.git /tmp/zappy
cd /tmp/zappy
sudo ./install.sh
```

### Manual Install

```bash
# Clone the repository
git clone https://github.com/KristjanPikhof/Zappy.git
cd Zappy

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

## Update

To update Zappy to the latest version:

```bash
curl -fsSL https://raw.githubusercontent.com/KristjanPikhof/Zappy/main/install.sh | sudo bash -s -- --update
```

Or if you have the repo cloned:

```bash
cd /path/to/Zappy
git pull
sudo ./install.sh --update
```

## Uninstall

To completely remove Zappy:

```bash
curl -fsSL https://raw.githubusercontent.com/KristjanPikhof/Zappy/main/install.sh | sudo bash -s -- --uninstall
```

Or locally:

```bash
sudo ./install.sh --uninstall
```

This removes `/opt/zappy` and the `zappy` command. Your nginx configs, Docker containers, and other installed tools remain untouched.

## Usage

```bash
zappy
```

Or run as a module:

```bash
python -m zappy
```

## Quick Start After Installation

```
┌─────────────────────────────────────┐
│    Zappy the VPS Toolbox v1.0       │
├─────────────────────────────────────┤
│  1. Nginx Management            →   │
│  2. Firewall Management         →   │
│  3. Security Hardening          →   │
│  4. Docker Setup                →   │
│  5. System Utilities            →   │
│  q. Quit                            │
└─────────────────────────────────────┘
```

## Documentation

- [New VPS Setup Guide](docs/NEW_VPS_SETUP.md) - First-time server setup
- [Better-CCFlare Setup](docs/BETTER_CCFLARE_SETUP.md) - Deploy better-ccflare with IP restriction
- [Nginx Templates](#nginx-templates) - Available configuration templates

## Nginx Templates

| Template | Use Case |
|----------|----------|
| `proxy` | Reverse proxy for backend services |
| `proxy-ws` | Reverse proxy with WebSocket support |
| `static` | Static file serving |
| `php` | PHP applications with php-fpm |
| `redirect` | HTTP redirects |

## Requirements

- Python 3.8+
- Linux operating system
- sudo privileges

## License

MIT License
