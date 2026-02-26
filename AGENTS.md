# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zappy is a comprehensive VPS management CLI tool for Linux servers. It provides an interactive menu-driven interface for managing Nginx, SSL certificates, firewalls, security hardening, Docker, and system utilities.

## Development Commands

```bash
# Install dependencies and run locally
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Run the tool
zappy
# or
python -m zappy

# Install globally (requires sudo)
sudo ./install.sh

# Update existing installation
sudo ./install.sh --update

# Uninstall
sudo ./install.sh --uninstall
```

## Architecture

### Entry Points
- `zappy/cli.py:main` - Main entry point, creates `VPSToolbox` instance and runs the menu loop
- `zappy/__main__.py` - Module entry point that calls `main()`

### Core Structure

```
zappy/
├── cli.py              # Main CLI application with menu system (VPSToolbox class)
├── config.py           # Global paths and configuration constants
├── modules/            # Feature modules organized by domain
│   ├── nginx/          # Nginx config management + Certbot SSL
│   ├── firewall/       # UFW/firewalld management
│   ├── security/       # SSH hardening, fail2ban, auto-updates
│   ├── docker/         # Docker + Dockge installation
│   └── system/         # Packages, shell setup, AiTermy, monitoring
└── utils/              # Shared utilities
    ├── command.py      # run_command(), run_sudo(), write_file_sudo()
    ├── distro.py       # Linux distro detection, package manager abstraction
    ├── ui.py           # Rich console UI helpers (print_header, select_from_list, etc.)
    └── validators.py   # Input validation functions
```

### Key Patterns

**Multi-distro support**: Uses `utils/distro.py` to detect Linux distributions and abstract package managers (apt, dnf, yum, pacman, apk, zypper). Use `detect_distro()` to get distro info and `get_install_command()` for cross-distro package installation.

**Sudo operations**: All privileged operations go through `utils/command.py`:
- `run_sudo()` for commands requiring root
- `write_file_sudo()` for writing to system files
- `verify_sudo()` to check sudo availability

**Nginx templates**: `modules/nginx/templates.py` provides config generators for proxy, proxy-ws, static, php, and redirect configurations.

**UI consistency**: All user interaction uses `utils/ui.py` which wraps the Rich library. Use `select_from_list()` for menus, `print_header()` for section headers, `print_error()`/`print_success()` for status messages.

### Configuration Paths (config.py)
- Nginx sites: `/etc/nginx/sites-available`, `/etc/nginx/sites-enabled`
- Backups: `/var/backups/zappy`
- Docker: `/opt/dockge`, `/opt/stacks`
- SSH: `/etc/ssh/sshd_config`

## Supported Distributions

Debian/Ubuntu, RHEL/CentOS/Fedora/Rocky/Alma, Arch Linux, Alpine Linux, openSUSE

## Dependencies

- Python 3.8+
- `rich>=13.0.0` (console UI)
- Requires sudo privileges to run

## Available Skills

### zappy-developer

Located at `.claude/skills/zappy-developer/SKILL.md`

Use this skill when:
- Adding new features or modules to Zappy
- Creating new nginx templates
- Adding menu items to the CLI
- Implementing firewall rules (UFW/firewalld)
- Adding system utilities or security features

The skill provides:
- Complete project structure reference
- Coding conventions and patterns
- Class templates for new modules
- UI patterns using rich library
- Git commit message conventions
- Testing checklist

**Trigger phrases**: "add feature", "new module", "extend zappy", "add nginx template"

## Git Conventions

Use conventional commits:
```
feat(module): add new feature
fix(nginx): resolve proxy_pass issue
docs(readme): update installation instructions
refactor(cli): simplify menu logic
```
