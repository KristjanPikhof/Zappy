"""Common tool installation (package manager + script installers)."""

from typing import List, Dict, Tuple

from ...utils.command import run_command, run_sudo, check_command_exists
from ...utils.distro import detect_distro, get_install_command, get_update_command, PackageManager
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    multi_select_from_list,
    pause,
    clear_screen,
    print_header,
)


# Package names and commands vary by distro
# command: the actual binary name to check (may differ from package name)
# command_apt: override command name for apt-based systems
TOOL_ORDER: List[str] = [
    "htop",
    "micro",
    "ncdu",
    "tmux",
    "tree",
    "jq",
    "bat",
    "ripgrep",
    "fd",
    "neofetch",
    "flatpak",
    "nvm-node",
    "opencode",
    "claude-code",
    "rust",
    "go",
    "brew",
]


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

    def _all_tools(self) -> List[str]:
        """Return catalog in deterministic order."""
        return TOOL_ORDER[:]

    def _is_script_tool(self, tool: str) -> bool:
        """Return whether tool uses script installer."""
        return tool in SCRIPT_TOOLS

    def _get_package_name(self, tool: str) -> str:
        """Get the package name for current distro.

        Args:
            tool: Tool name

        Returns:
            Package name for current distro
        """
        if self._is_script_tool(tool):
            return SCRIPT_TOOLS[tool].get("command", tool)

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
        if tool == "nvm-node":
            marker_rc, _, _ = run_command(["bash", "-lc", "test -s \"$HOME/.nvm/nvm.sh\""])
            if marker_rc != 0:
                return False
            return check_command_exists("node")

        cmd = self._get_command_name(tool)
        return check_command_exists(cmd)

    def _display_name(self, tool: str) -> str:
        """Get display name for tool."""
        if self._is_script_tool(tool):
            return SCRIPT_TOOLS[tool].get("label", tool)
        return tool

    def _description(self, tool: str) -> str:
        """Get tool description."""
        if self._is_script_tool(tool):
            return SCRIPT_TOOLS[tool]["description"]
        return COMMON_PACKAGES[tool]["description"]

    def _install_nvm_node(self) -> bool:
        """Install NVM and Node.js 24."""
        cmd = (
            "PROFILE=/dev/null curl -o- "
            "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash && "
            "bash -lc 'export NVM_DIR=\"$HOME/.nvm\"; "
            "[ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\"; "
            "nvm install 24; nvm alias default 24'"
        )
        rc, _, stderr = run_command(["bash", "-lc", cmd])
        if rc != 0:
            print_error(f"Failed to install nvm-node: {stderr.strip()}")
            return False
        return self._is_installed("nvm-node")

    def _install_opencode(self) -> bool:
        """Install Opencode CLI."""
        rc, _, stderr = run_command(
            ["bash", "-lc", "curl -fsSL https://opencode.ai/install | bash"]
        )
        if rc != 0:
            print_error(f"Failed to install opencode: {stderr.strip()}")
            return False
        return self._is_installed("opencode")

    def _install_claude_code(self) -> bool:
        """Install Claude Code CLI."""
        rc, _, stderr = run_command(
            ["bash", "-lc", "curl -fsSL https://claude.ai/install.sh | bash"]
        )
        if rc != 0:
            print_error(f"Failed to install claude-code: {stderr.strip()}")
            return False
        return self._is_installed("claude-code")

    def _install_rust(self) -> bool:
        """Install Rust via rustup."""
        rc, _, stderr = run_command(
            [
                "bash",
                "-lc",
                "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
            ]
        )
        if rc != 0:
            print_error(f"Failed to install rust: {stderr.strip()}")
            return False
        return self._is_installed("rust")

    def _install_go(self) -> bool:
        """Install latest stable Go from official tarball."""
        rc, arch_out, stderr = run_command(["uname", "-m"])
        if rc != 0:
            print_error(f"Failed to detect architecture: {stderr.strip()}")
            return False

        arch = arch_out.strip()
        arch_map = {
            "x86_64": "amd64",
            "aarch64": "arm64",
            "arm64": "arm64",
        }
        go_arch = arch_map.get(arch)
        if not go_arch:
            print_error(f"Unsupported architecture for Go install: {arch}")
            return False

        rc, version_out, stderr = run_command(
            ["bash", "-lc", "curl -fsSL 'https://go.dev/VERSION?m=text'"]
        )
        if rc != 0:
            print_error(f"Failed to fetch latest Go version: {stderr.strip()}")
            return False

        version = version_out.splitlines()[0].strip() if version_out else ""
        if not version.startswith("go"):
            print_error("Could not determine latest Go version from go.dev")
            return False

        tarball = f"/tmp/{version}.linux-{go_arch}.tar.gz"
        url = f"https://go.dev/dl/{version}.linux-{go_arch}.tar.gz"

        rc, _, stderr = run_command(["curl", "-fsSL", "-o", tarball, url])
        if rc != 0:
            print_error(f"Failed to download Go tarball: {stderr.strip()}")
            return False

        success, _, _ = run_sudo(["rm", "-rf", "/usr/local/go"])
        if not success:
            return False

        success, _, _ = run_sudo(["tar", "-C", "/usr/local", "-xzf", tarball])
        run_command(["rm", "-f", tarball])
        if not success:
            return False

        rc, _, _ = run_command(["test", "-x", "/usr/local/go/bin/go"])
        if rc != 0:
            print_error("Go install verification failed: /usr/local/go/bin/go not found")
            return False

        return self._is_installed("go") or rc == 0

    def _install_brew(self) -> bool:
        """Install Homebrew."""
        rc, _, stderr = run_command(
            [
                "bash",
                "-lc",
                "NONINTERACTIVE=1 /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
            ]
        )
        if rc != 0:
            print_error(f"Failed to install brew: {stderr.strip()}")
            return False
        return self._is_installed("brew")

    def _install_script_tool(self, tool: str) -> bool:
        """Install a single script-based tool."""
        installers = {
            "nvm-node": self._install_nvm_node,
            "opencode": self._install_opencode,
            "claude-code": self._install_claude_code,
            "rust": self._install_rust,
            "go": self._install_go,
            "brew": self._install_brew,
        }
        installer = installers.get(tool)
        if not installer:
            print_error(f"No installer configured for {tool}")
            return False
        return installer()

    def _build_install_plan(self, selected_tools: List[str]) -> Tuple[List[str], List[str]]:
        """Return (already_installed, install_now) for selected tools."""
        already_installed = [tool for tool in selected_tools if self._is_installed(tool)]
        install_now = [tool for tool in selected_tools if tool not in already_installed]
        return already_installed, install_now

    def _execute_install_batch(self, tools: List[str]) -> bool:
        """Install selected tools, continue on failures, print summary."""
        pm_tools = [tool for tool in tools if not self._is_script_tool(tool)]
        if pm_tools:
            console.print("\n[dim]Updating package list...[/dim]")
            update_cmd = get_update_command(self.pm)
            run_sudo(update_cmd, show_command=False)

        success_tools: List[str] = []
        failed_tools: List[str] = []

        for tool in tools:
            console.print(f"\n[dim]Installing {self._display_name(tool)}...[/dim]")
            ok = self.install_package(tool)
            if ok:
                success_tools.append(tool)
            else:
                failed_tools.append(tool)

        console.print()
        print_info("Batch install summary:")
        console.print(f"  [green]Installed:[/green] {len(success_tools)}")
        console.print(f"  [red]Failed:[/red] {len(failed_tools)}")
        if success_tools:
            console.print(
                "  [green]Success tools:[/green] "
                + ", ".join(self._display_name(t) for t in success_tools)
            )
        if failed_tools:
            console.print(
                "  [red]Failed tools:[/red] "
                + ", ".join(self._display_name(t) for t in failed_tools)
            )

        pause()
        return len(failed_tools) == 0

    def install_menu(self) -> bool:
        """Show interactive package installation menu.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Install Common Tools")

        console.print(f"Package Manager: {self.pm.value}")
        console.print()

        # Show full catalog with install status
        tools = self._all_tools()
        items: List[str] = []
        for name in tools:
            installed = self._is_installed(name)
            status = "[green]✓[/green]" if installed else "[dim]○[/dim]"
            install_kind = "script" if self._is_script_tool(name) else self.pm.value
            items.append(
                f"{status} {self._display_name(name)} - {self._description(name)} [dim]({install_kind})[/dim]"
            )

        missing_indices = [i for i, tool in enumerate(tools) if not self._is_installed(tool)]
        special_keywords = {
            "all": list(range(len(tools))),
            "*": list(range(len(tools))),
            "missing": missing_indices,
            "m": missing_indices,
        }

        choices = multi_select_from_list(
            items,
            title="Select tools to install",
            allow_back=True,
            back_value="b",
            special_keywords=special_keywords,
        )
        if choices is None:
            return False

        if not choices:
            print_warning("No tools selected.")
            pause()
            return False

        selected_tools = [tools[i] for i in choices]
        already_installed, install_now = self._build_install_plan(selected_tools)

        console.print()
        print_info("Install plan preview:")
        console.print(f"  Selected: {len(selected_tools)}")
        console.print(f"  Already installed (skip): {len(already_installed)}")
        console.print(f"  Install now: {len(install_now)}")
        if install_now:
            console.print(
                "  [cyan]Install-now list:[/cyan] "
                + ", ".join(self._display_name(t) for t in install_now)
            )

        if not install_now:
            print_success("All selected tools are already installed.")
            pause()
            return True

        if not confirm("Proceed with installation?", default=True):
            return False

        return self._execute_install_batch(install_now)

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

        if self._is_script_tool(tool):
            return self._install_script_tool(tool)

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

        # Find missing tools
        missing = [tool for tool in self._all_tools() if not self._is_installed(tool)]

        if not missing:
            print_success("All tools are already installed!")
            pause()
            return True

        console.print(
            "Missing tools: " + ", ".join(self._display_name(tool) for tool in missing)
        )
        console.print()

        if not confirm(f"Install {len(missing)} missing tools?", default=True):
            return False

        return self._execute_install_batch(missing)

    def show_installed(self) -> bool:
        """Show which tools are installed.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Installed Tools")

        for name in self._all_tools():
            installed = self._is_installed(name)
            cmd = self._get_command_name(name)
            cmd_info = f" (cmd: {cmd})" if cmd != name else ""
            if installed:
                console.print(
                    f"  [green]✓[/green] {self._display_name(name)}{cmd_info} - {self._description(name)}"
                )
            else:
                console.print(
                    f"  [dim]○[/dim] {self._display_name(name)}{cmd_info} - {self._description(name)}"
                )

        pause()
        return True
