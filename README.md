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
curl -fsSL https://raw.githubusercontent.com/KristjanPikhof/vps-toolbox/main/install.sh | bash
```

### Manual Install

```bash
# Clone the repository
git clone https://github.com/KristjanPikhof/vps-toolbox.git
cd vps-toolbox

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

## Usage

```bash
vps-toolbox
```

Or run as a module:

```bash
python -m vps_toolbox
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
