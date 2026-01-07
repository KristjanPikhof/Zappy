---
name: zappy-developer
description: Add features, fix bugs, and extend the Zappy VPS Toolbox. Use when adding new modules, nginx templates, menu options, firewall rules, security features, or system utilities to Zappy. Triggers on "add feature", "new module", "extend zappy", "add to zappy".
---

# Zappy VPS Toolbox Developer

This skill helps you develop and extend the Zappy VPS Toolbox following established patterns and conventions.

## Project Structure

```
zappy/
├── __init__.py
├── __main__.py           # Entry point (python -m zappy)
├── cli.py                # Main menu and CLI interface
├── config.py             # Global configuration and paths
├── utils/
│   ├── command.py        # run_sudo, run_command, check_command_exists
│   ├── distro.py         # Linux distribution detection
│   ├── ui.py             # Terminal UI (rich library)
│   └── validators.py     # Input validation functions
├── modules/
│   ├── nginx/
│   │   ├── manager.py    # Domain CRUD operations
│   │   ├── certbot.py    # SSL certificate management
│   │   └── templates.py  # Nginx config templates
│   ├── firewall/
│   │   └── manager.py    # UFW/firewalld abstraction
│   ├── security/
│   │   ├── ssh.py        # SSH hardening
│   │   ├── fail2ban.py   # Fail2ban setup
│   │   └── updates.py    # Automatic security updates
│   ├── docker/
│   │   ├── installer.py  # Docker installation
│   │   └── dockge.py     # Dockge deployment
│   └── system/
│       ├── packages.py   # Common tools installation
│       ├── shell.py      # zsh + oh-my-zsh setup
│       ├── aitermy.py    # AiTermy installation
│       └── monitoring.py # System monitoring
├── install.sh            # Distribution-aware installer
├── setup.py              # pip installation
└── docs/                 # Documentation guides
```

## Coding Conventions

### Imports

```python
from ...utils.command import run_sudo, run_command, check_command_exists
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    prompt,
    select_from_list,
    pause,
    clear_screen,
    print_header,
)
```

### Class Pattern

Every module follows this pattern:

```python
class FeatureManager:
    """Manages feature functionality."""

    def __init__(self):
        # Initialize any state
        pass

    def is_installed(self) -> bool:
        """Check if feature is installed."""
        return check_command_exists("feature")

    def install(self) -> bool:
        """Install the feature.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Install Feature")

        if self.is_installed():
            print_info("Feature is already installed.")
            pause()
            return True

        # Installation logic
        success, _, _ = run_sudo(["apt", "install", "-y", "feature"])

        if success:
            print_success("Feature installed!")
        else:
            print_error("Failed to install feature.")

        pause()
        return success

    def show_status(self) -> bool:
        """Show feature status."""
        clear_screen()
        print_header("Feature Status")

        if not self.is_installed():
            print_warning("Feature is not installed.")
            if confirm("Install now?"):
                return self.install()
            pause()
            return False

        # Show status info
        _, stdout, _ = run_sudo(["feature", "--status"], show_command=False)
        console.print(stdout)

        pause()
        return True
```

### Running Commands

```python
# Run with sudo (returns tuple: success, stdout, stderr)
success, stdout, stderr = run_sudo(["systemctl", "status", "nginx"], show_command=False)

# Run without sudo
returncode, stdout, stderr = run_command(["git", "status"])

# Check if command exists
if check_command_exists("docker"):
    print_info("Docker is available")
```

### User Interface

```python
# Headers and messages
clear_screen()
print_header("Feature Name")
print_success("Operation completed!")
print_error("Something went wrong.")
print_warning("Be careful!")
print_info("Informational message.")

# User input
name = prompt("Enter name").strip()
name = prompt("Enter name", default="default_value").strip()

# Confirmation
if confirm("Proceed?", default=True):
    # do action
    pass

# Menu selection (returns index or None if back)
options = ["Option 1", "Option 2", "Option 3"]
choice = select_from_list(options, "Select option:")
if choice is None:
    return  # User pressed back

# Wait for user
pause()
```

### Adding to CLI Menu

Edit `cli.py` to add menu items:

```python
def feature_menu(self):
    """Display feature menu."""
    while True:
        clear_screen()
        print_header("Feature Name")

        options = [
            "Show status",
            "Install feature",
            "Configure feature",
        ]

        choice = select_from_list(options, "Select action:")

        if choice is None:
            return

        if choice == 0:
            self.feature.show_status()
        elif choice == 1:
            self.feature.install()
        elif choice == 2:
            self.feature.configure()
```

Then add to main menu in `main_menu()` method.

## Adding New Nginx Templates

Edit `zappy/modules/nginx/templates.py`:

```python
TEMPLATE_TYPES = {
    "proxy": "Reverse Proxy (default)",
    "proxy-ws": "Reverse Proxy with WebSocket support",
    "static": "Static file serving",
    "php": "PHP application (php-fpm)",
    "redirect": "HTTP redirect",
    "new-type": "Description of new type",  # Add here
}

def _template_new_type(
    server_name: str,
    **kwargs,
) -> str:
    """New template description."""
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    # Configuration here

    error_log {NGINX_LOG_DIR}/{server_name}_error.log;
    access_log {NGINX_LOG_DIR}/{server_name}_access.log;
}}
"""
```

Then add to `templates` dict in `get_template()` function.

## Adding Firewall Rules

The firewall manager supports both UFW and firewalld:

```python
# In firewall/manager.py
if fw_type == FirewallType.UFW:
    success, _, _ = run_sudo(["ufw", "allow", f"{port}/tcp"])
else:  # firewalld
    success, _, _ = run_sudo([
        "firewall-cmd", "--add-port", f"{port}/tcp", "--permanent"
    ])
    if success:
        run_sudo(["firewall-cmd", "--reload"], show_command=False)
```

## Configuration Paths

Add new paths in `config.py`:

```python
# Existing paths
NGINX_SITES_AVAILABLE = "/etc/nginx/sites-available"
BACKUP_DIR = Path("/var/backups/zappy")
DOCKGE_DIR = Path("/opt/dockge")

# Add new paths
NEW_FEATURE_DIR = Path("/opt/new-feature")
NEW_FEATURE_CONFIG = Path("/etc/new-feature/config.conf")
```

## Backup Before Modifying Configs

```python
from ...config import ensure_backup_dir, get_backup_path
from ...utils.command import backup_file

# Create backup before modifying
ensure_backup_dir("feature")
backup_path = get_backup_path("feature", "config")
backup_file("/etc/feature/config", str(backup_path))
```

## Git Commit Convention

Use conventional commits:

```
feat(module): add new feature
fix(nginx): resolve proxy_pass issue
docs(readme): update installation instructions
refactor(cli): simplify menu logic
chore(deps): update requirements
```

## Testing Checklist

Before committing:

1. [ ] Code follows existing patterns
2. [ ] UI uses rich library functions
3. [ ] Commands use run_sudo/run_command
4. [ ] Success/error messages are clear
5. [ ] Menu items added to cli.py
6. [ ] Backups created before config changes
7. [ ] Both UFW and firewalld supported (if firewall-related)
8. [ ] Works on Debian/Ubuntu (apt)
9. [ ] Commit message follows convention

## Quick Reference

| Task | Location |
|------|----------|
| Add module | `zappy/modules/category/name.py` |
| Add menu | `zappy/cli.py` |
| Add nginx template | `zappy/modules/nginx/templates.py` |
| Add config path | `zappy/config.py` |
| Add validator | `zappy/utils/validators.py` |
| Add docs | `docs/GUIDE_NAME.md` |
| Update install | `install.sh` |
