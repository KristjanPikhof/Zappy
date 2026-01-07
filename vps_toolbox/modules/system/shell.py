"""Shell setup (zsh + oh-my-zsh)."""

import os
from pathlib import Path

from ...utils.command import run_sudo, run_command, check_command_exists
from ...utils.distro import get_install_command, get_package_manager
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    pause,
    clear_screen,
    print_header,
)


class ShellSetup:
    """Manages shell configuration."""

    def __init__(self):
        self.oh_my_zsh_url = "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"

    def is_zsh_installed(self) -> bool:
        """Check if zsh is installed.

        Returns:
            True if installed, False otherwise
        """
        return check_command_exists("zsh")

    def is_oh_my_zsh_installed(self) -> bool:
        """Check if oh-my-zsh is installed.

        Returns:
            True if installed, False otherwise
        """
        return Path.home().joinpath(".oh-my-zsh").exists()

    def setup(self) -> bool:
        """Run the complete shell setup wizard.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Shell Setup")

        console.print("[bold]This will set up zsh with oh-my-zsh.[/bold]")
        console.print()

        if not self.is_zsh_installed():
            if not confirm("zsh is not installed. Install it?", default=True):
                return False
            if not self._install_zsh():
                pause()
                return False

        if not self.is_oh_my_zsh_installed():
            if not confirm("Install oh-my-zsh?", default=True):
                return False
            if not self._install_oh_my_zsh():
                pause()
                return False
        else:
            print_info("oh-my-zsh is already installed.")

        # Offer to set as default shell
        current_shell = os.environ.get("SHELL", "")
        if "zsh" not in current_shell:
            if confirm("Set zsh as your default shell?"):
                self._set_default_shell()

        # Show plugin recommendations
        self._show_plugin_recommendations()

        pause()
        return True

    def _install_zsh(self) -> bool:
        """Install zsh.

        Returns:
            True on success, False on failure
        """
        console.print("\n[dim]Installing zsh...[/dim]")

        pm = get_package_manager()
        install_cmd = get_install_command(["zsh"], pm)
        success, _, _ = run_sudo(install_cmd)

        if success:
            print_success("zsh installed.")
        else:
            print_error("Failed to install zsh.")

        return success

    def _install_oh_my_zsh(self) -> bool:
        """Install oh-my-zsh.

        Returns:
            True on success, False on failure
        """
        console.print("\n[dim]Installing oh-my-zsh...[/dim]")

        # oh-my-zsh installer runs as user, not root
        success, _, stderr = run_command([
            "sh", "-c",
            f'RUNZSH=no CHSH=no sh -c "$(curl -fsSL {self.oh_my_zsh_url})"'
        ])

        if success or self.is_oh_my_zsh_installed():
            print_success("oh-my-zsh installed.")
            return True

        print_error("Failed to install oh-my-zsh.")
        console.print(f"[dim]{stderr}[/dim]")
        return False

    def _set_default_shell(self) -> bool:
        """Set zsh as default shell.

        Returns:
            True on success, False on failure
        """
        console.print("\n[dim]Setting zsh as default shell...[/dim]")

        username = os.environ.get("SUDO_USER") or os.environ.get("USER")
        zsh_path = "/bin/zsh"

        # Find zsh path
        _, stdout, _ = run_command(["which", "zsh"])
        if stdout.strip():
            zsh_path = stdout.strip()

        success, _, _ = run_sudo(["chsh", "-s", zsh_path, username])

        if success:
            print_success(f"Default shell set to zsh for {username}.")
            print_info("Log out and back in for changes to take effect.")
        else:
            print_error("Failed to change default shell.")

        return success

    def _show_plugin_recommendations(self):
        """Show recommended oh-my-zsh plugins."""
        console.print("\n[bold]Recommended Plugins:[/bold]")
        console.print("Add these to ~/.zshrc in the plugins=(...) section:")
        console.print()
        console.print("  [cyan]git[/cyan] - Git aliases and completions")
        console.print("  [cyan]docker[/cyan] - Docker completions")
        console.print("  [cyan]docker-compose[/cyan] - Docker Compose completions")
        console.print("  [cyan]sudo[/cyan] - Press ESC twice to add sudo")
        console.print("  [cyan]history[/cyan] - History search shortcuts")
        console.print()
        console.print("[bold]Popular External Plugins:[/bold]")
        console.print("  [cyan]zsh-autosuggestions[/cyan] - Fish-like suggestions")
        console.print("  [cyan]zsh-syntax-highlighting[/cyan] - Syntax colors")
        console.print()
        print_info("After installing, run: source ~/.zshrc")

    def show_status(self) -> bool:
        """Show shell configuration status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Shell Status")

        current_shell = os.environ.get("SHELL", "Unknown")
        console.print(f"Current shell: {current_shell}")
        console.print()

        # zsh status
        if self.is_zsh_installed():
            _, zsh_version, _ = run_command(["zsh", "--version"])
            console.print(f"[green]✓[/green] zsh: {zsh_version.strip()}")
        else:
            console.print("[red]✗[/red] zsh: Not installed")

        # oh-my-zsh status
        if self.is_oh_my_zsh_installed():
            console.print("[green]✓[/green] oh-my-zsh: Installed")

            # Show current theme
            zshrc = Path.home() / ".zshrc"
            if zshrc.exists():
                content = zshrc.read_text()
                for line in content.split("\n"):
                    if line.startswith("ZSH_THEME="):
                        theme = line.split("=", 1)[1].strip('"\'')
                        console.print(f"    Theme: {theme}")
                        break
        else:
            console.print("[red]✗[/red] oh-my-zsh: Not installed")

        pause()
        return True
