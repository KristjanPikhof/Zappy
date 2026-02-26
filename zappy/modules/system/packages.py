"""Common package installation."""

from typing import List, Dict

from ...utils.command import run_sudo, check_command_exists
from ...utils.distro import detect_distro, get_install_command, get_update_command, PackageManager
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    select_from_list,
    pause,
    clear_screen,
    print_header,
)


# Package names and commands vary by distro
# command: the actual binary name to check (may differ from package name)
# command_apt: override command name for apt-based systems
COMMON_PACKAGES: Dict[str, Dict[str, str]] = {
    "htop": {
        "description": "Interactive process viewer",
        "command": "htop",
        "apt": "htop",
        "dnf": "htop",
        "pacman": "htop",
        "apk": "htop",
    },
    "micro": {
        "description": "Modern terminal text editor",
        "command": "micro",
        "apt": "micro",
        "dnf": "micro",
        "pacman": "micro",
        "apk": "micro",
    },
    "ncdu": {
        "description": "Disk usage analyzer",
        "command": "ncdu",
        "apt": "ncdu",
        "dnf": "ncdu",
        "pacman": "ncdu",
        "apk": "ncdu",
    },
    "tmux": {
        "description": "Terminal multiplexer",
        "command": "tmux",
        "apt": "tmux",
        "dnf": "tmux",
        "pacman": "tmux",
        "apk": "tmux",
    },
    "tree": {
        "description": "Directory tree viewer",
        "command": "tree",
        "apt": "tree",
        "dnf": "tree",
        "pacman": "tree",
        "apk": "tree",
    },
    "jq": {
        "description": "JSON processor",
        "command": "jq",
        "apt": "jq",
        "dnf": "jq",
        "pacman": "jq",
        "apk": "jq",
    },
    "bat": {
        "description": "Cat with syntax highlighting",
        "command": "bat",
        "command_apt": "batcat",  # Different command name on Debian/Ubuntu
        "apt": "bat",
        "dnf": "bat",
        "pacman": "bat",
        "apk": "bat",
    },
    "ripgrep": {
        "description": "Fast recursive grep",
        "command": "rg",  # Command is 'rg' not 'ripgrep'
        "apt": "ripgrep",
        "dnf": "ripgrep",
        "pacman": "ripgrep",
        "apk": "ripgrep",
    },
    "fd": {
        "description": "Fast find alternative",
        "command": "fd",
        "command_apt": "fdfind",  # Different command name on Debian/Ubuntu
        "apt": "fd-find",
        "dnf": "fd-find",
        "pacman": "fd",
        "apk": "fd",
    },
    "neofetch": {
        "description": "System info display",
        "command": "neofetch",
        "apt": "neofetch",
        "dnf": "neofetch",
        "pacman": "neofetch",
        "apk": "neofetch",
    },
    "flatpak": {
        "description": "Flatpak app platform",
        "command": "flatpak",
        "apt": "flatpak",
        "dnf": "flatpak",
        "yum": "flatpak",
        "pacman": "flatpak",
        "apk": "flatpak",
        "zypper": "flatpak",
    },
}


SCRIPT_TOOLS: Dict[str, Dict[str, str]] = {
    "nvm-node": {
        "label": "NVM + Node.js 24",
        "description": "Install NVM and Node.js 24",
        "command": "node",
    },
    "opencode": {
        "label": "Opencode",
        "description": "Install Opencode CLI",
        "command": "opencode",
    },
    "claude-code": {
        "label": "Claude Code",
        "description": "Install Claude Code CLI",
        "command": "claude",
    },
    "rust": {
        "label": "Rust",
        "description": "Install Rust via rustup",
        "command": "rustc",
    },
    "go": {
        "label": "Go",
        "description": "Install Go (official tarball)",
        "command": "go",
    },
    "brew": {
        "label": "Homebrew",
        "description": "Install Homebrew",
        "command": "brew",
    },
}


class PackagesManager:
    """Manages common package installation."""

    def __init__(self):
        self.distro = detect_distro()
        self.pm = self.distro.package_manager

    def _get_package_name(self, tool: str) -> str:
        """Get the package name for current distro.

        Args:
            tool: Tool name

        Returns:
            Package name for current distro
        """
        pkg_info = COMMON_PACKAGES.get(tool, {})
        pm_key = self.pm.value

        return pkg_info.get(pm_key, tool)

    def _get_command_name(self, tool: str) -> str:
        """Get the command name to check if tool is installed.

        Args:
            tool: Tool name

        Returns:
            Command name for current distro
        """
        pkg_info = COMMON_PACKAGES.get(tool, {})

        # Check for distro-specific command name override
        if self.pm == PackageManager.APT:
            cmd = pkg_info.get("command_apt")
            if cmd:
                return cmd

        return pkg_info.get("command", tool)

    def _is_installed(self, tool: str) -> bool:
        """Check if a tool is installed.

        Args:
            tool: Tool name

        Returns:
            True if installed
        """
        cmd = self._get_command_name(tool)
        return check_command_exists(cmd)

    def install_menu(self) -> bool:
        """Show interactive package installation menu.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Install Common Tools")

        console.print(f"Package Manager: {self.pm.value}")
        console.print()

        # Show available packages with install status
        items = []
        for name, info in COMMON_PACKAGES.items():
            installed = self._is_installed(name)
            status = "[green]✓[/green]" if installed else "[dim]○[/dim]"
            items.append(f"{status} {name} - {info['description']}")

        items.append("[bold]Install all missing packages[/bold]")

        choice = select_from_list(items, "Select package to install:")
        if choice is None:
            return False

        if choice == len(items) - 1:
            # Install all
            return self.install_all()

        # Install single package
        package_name = list(COMMON_PACKAGES.keys())[choice]
        return self.install_package(package_name)

    def install_package(self, tool: str) -> bool:
        """Install a single package.

        Args:
            tool: Tool name

        Returns:
            True on success, False on failure
        """
        if self._is_installed(tool):
            print_info(f"{tool} is already installed.")
            return True

        package = self._get_package_name(tool)
        console.print(f"\n[dim]Installing {tool} ({package})...[/dim]")

        install_cmd = get_install_command([package], self.pm)
        success, _, _ = run_sudo(install_cmd)

        if success:
            print_success(f"{tool} installed.")
        else:
            print_error(f"Failed to install {tool}.")

        return success

    def install_all(self) -> bool:
        """Install all missing packages.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Installing All Tools")

        # Find missing packages
        missing = []
        for tool in COMMON_PACKAGES:
            if not self._is_installed(tool):
                missing.append(tool)

        if not missing:
            print_success("All packages are already installed!")
            pause()
            return True

        console.print(f"Missing packages: {', '.join(missing)}")
        console.print()

        if not confirm(f"Install {len(missing)} packages?", default=True):
            return False

        # Update package list first
        console.print("\n[dim]Updating package list...[/dim]")
        update_cmd = get_update_command(self.pm)
        run_sudo(update_cmd, show_command=False)

        # Install each package
        success_count = 0
        for tool in missing:
            if self.install_package(tool):
                success_count += 1

        console.print()
        print_success(f"Installed {success_count}/{len(missing)} packages.")
        pause()
        return True

    def show_installed(self) -> bool:
        """Show which tools are installed.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Installed Tools")

        for name, info in COMMON_PACKAGES.items():
            installed = self._is_installed(name)
            cmd = self._get_command_name(name)
            cmd_info = f" (cmd: {cmd})" if cmd != name else ""
            if installed:
                console.print(f"  [green]✓[/green] {name}{cmd_info} - {info['description']}")
            else:
                console.print(f"  [dim]○[/dim] {name}{cmd_info} - {info['description']}")

        pause()
        return True
