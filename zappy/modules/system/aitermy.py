"""AiTermy AI terminal assistant installation."""

from pathlib import Path

from ...config import AITERMY_DIR
from ...utils.command import run_sudo, run_command, check_command_exists
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


class AiTermyInstaller:
    """Manages AiTermy installation."""

    REPO_URL = "https://github.com/KristjanPikhof/AiTermy.git"

    def __init__(self):
        self.install_dir = AITERMY_DIR

    def is_installed(self) -> bool:
        """Check if AiTermy is installed.

        Returns:
            True if installed, False otherwise
        """
        return (self.install_dir / "install.sh").exists()

    def is_configured(self) -> bool:
        """Check if AiTermy is configured in shell.

        Returns:
            True if configured, False otherwise
        """
        # Check if 'ai' function exists in zshrc or bashrc
        zshrc = Path.home() / ".zshrc"
        bashrc = Path.home() / ".bashrc"

        for rc_file in [zshrc, bashrc]:
            if rc_file.exists():
                content = rc_file.read_text()
                if "aitermy" in content.lower() or "ai()" in content:
                    return True

        return False

    def install(self) -> bool:
        """Install AiTermy.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Install AiTermy")

        console.print("[bold]AiTermy - AI Terminal Assistant[/bold]")
        console.print("https://github.com/KristjanPikhof/AiTermy")
        console.print()

        # Check prerequisites
        if not check_command_exists("git"):
            print_error("Git is not installed.")
            print_info("Install git first: sudo apt install git")
            pause()
            return False

        if not check_command_exists("python3"):
            print_error("Python 3 is not installed.")
            pause()
            return False

        if self.is_installed():
            print_info("AiTermy is already installed.")
            if self.is_configured():
                print_success("AiTermy is configured.")
            else:
                if confirm("Run installer to configure?"):
                    return self._run_installer()
            pause()
            return True

        # Clone repository
        console.print("\n[dim]Cloning AiTermy repository...[/dim]")

        # Create install directory
        run_sudo(["mkdir", "-p", str(self.install_dir.parent)])

        success, _, stderr = run_sudo([
            "git", "clone", self.REPO_URL, str(self.install_dir)
        ])

        if not success:
            print_error("Failed to clone AiTermy repository.")
            console.print(f"[dim]{stderr}[/dim]")
            pause()
            return False

        print_success("Repository cloned.")

        # Run installer
        return self._run_installer()

    def _run_installer(self) -> bool:
        """Run the AiTermy installer script.

        Returns:
            True on success, False on failure
        """
        console.print("\n[bold]Running AiTermy installer...[/bold]")
        console.print()
        print_info("The installer will ask for:")
        console.print("  1. Your OpenRouter API key")
        console.print("  2. Your preferred AI model")
        console.print()

        if not confirm("Continue with installation?", default=True):
            return False

        # Make installer executable
        run_sudo(["chmod", "+x", str(self.install_dir / "install.sh")])

        # Run installer (interactive)
        import subprocess
        result = subprocess.run(
            ["bash", str(self.install_dir / "install.sh")],
            cwd=str(self.install_dir)
        )

        if result.returncode == 0:
            print_success("AiTermy installed!")
            console.print()
            print_info("To start using AiTermy, run:")
            console.print("  source ~/.zshrc  # or ~/.bashrc")
            console.print("  ai \"Hello!\"")
        else:
            print_warning("Installation may have issues. Check the output above.")

        pause()
        return result.returncode == 0

    def update(self) -> bool:
        """Update AiTermy to latest version.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Update AiTermy")

        if not self.is_installed():
            print_warning("AiTermy is not installed.")
            if confirm("Install now?"):
                return self.install()
            pause()
            return False

        console.print("[dim]Updating AiTermy...[/dim]")

        # Use sudo since repo was cloned with sudo
        success, _, stderr = run_sudo([
            "git", "-C", str(self.install_dir), "pull"
        ], show_command=False)

        if success:
            print_success("AiTermy updated!")
        else:
            print_error("Failed to update AiTermy.")
            console.print(f"[dim]{stderr}[/dim]")

        pause()
        return success

    def show_status(self) -> bool:
        """Show AiTermy status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("AiTermy Status")

        if not self.is_installed():
            print_warning("AiTermy is not installed.")
            if confirm("Install now?"):
                return self.install()
        else:
            print_success(f"AiTermy installed at: {self.install_dir}")

            if self.is_configured():
                print_success("Shell integration: Configured")
            else:
                print_warning("Shell integration: Not configured")
                print_info("Run the installer to configure shell integration.")

            # Show version/last commit
            success, stdout, _ = run_command([
                "git", "-C", str(self.install_dir), "log", "-1", "--format=%h %s"
            ])
            if success:
                console.print(f"Latest commit: {stdout.strip()}")

        pause()
        return True

    def uninstall(self) -> bool:
        """Uninstall AiTermy.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Uninstall AiTermy")

        if not self.is_installed():
            print_info("AiTermy is not installed.")
            pause()
            return True

        print_warning("This will remove AiTermy from your system.")
        print_info("You may need to manually remove the shell integration from ~/.zshrc or ~/.bashrc")

        if not confirm("Proceed with uninstall?"):
            return False

        success, _, _ = run_sudo(["rm", "-rf", str(self.install_dir)])

        if success:
            print_success("AiTermy uninstalled.")
            print_info("Remember to remove the AiTermy lines from your shell rc file.")
        else:
            print_error("Failed to remove AiTermy directory.")

        pause()
        return success
