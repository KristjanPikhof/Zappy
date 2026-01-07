"""Dockge container manager installation."""

from pathlib import Path

from ...config import DOCKGE_DIR, DOCKER_STACKS_DIR
from ...utils.command import run_sudo, run_command, check_command_exists, write_file_sudo
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    prompt,
    pause,
    clear_screen,
    print_header,
)
from ...utils.validators import validate_port


class DockgeManager:
    """Manages Dockge installation."""

    def __init__(self):
        self.dockge_dir = DOCKGE_DIR
        self.stacks_dir = DOCKER_STACKS_DIR
        self.default_port = "5001"

    def is_installed(self) -> bool:
        """Check if Dockge is installed.

        Returns:
            True if installed, False otherwise
        """
        compose_file = self.dockge_dir / "compose.yaml"
        return compose_file.exists()

    def is_running(self) -> bool:
        """Check if Dockge is running.

        Returns:
            True if running, False otherwise
        """
        if not check_command_exists("docker"):
            return False

        success, stdout, _ = run_command([
            "docker", "ps", "--filter", "name=dockge", "--format", "{{.Names}}"
        ])

        return success and "dockge" in stdout

    def install(self) -> bool:
        """Install Dockge.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Install Dockge")

        # Check Docker
        if not check_command_exists("docker"):
            print_error("Docker is not installed.")
            print_info("Please install Docker first.")
            pause()
            return False

        if self.is_installed():
            print_info("Dockge is already installed.")
            if self.is_running():
                print_success("Dockge is running.")
            else:
                if confirm("Start Dockge?"):
                    self.start()
            pause()
            return True

        # Get port
        port = prompt(f"Enter Dockge port", default=self.default_port).strip()
        is_valid, error = validate_port(port)
        if not is_valid:
            print_error(error)
            pause()
            return False

        # Get stacks directory
        stacks_path = prompt(
            "Enter stacks directory",
            default=str(self.stacks_dir)
        ).strip()

        console.print("\n[bold]Installation Settings:[/bold]")
        console.print(f"  Port: {port}")
        console.print(f"  Dockge directory: {self.dockge_dir}")
        console.print(f"  Stacks directory: {stacks_path}")

        if not confirm("\nProceed with installation?", default=True):
            return False

        # Create directories
        console.print("\n[dim]Creating directories...[/dim]")
        run_sudo(["mkdir", "-p", str(self.dockge_dir)])
        run_sudo(["mkdir", "-p", stacks_path])

        # Download compose.yaml
        console.print("[dim]Downloading Dockge compose.yaml...[/dim]")
        compose_url = f"https://dockge.kuma.pet/compose.yaml?port={port}&stacksPath={stacks_path}"

        success, _, _ = run_command([
            "curl", "-fsSL", compose_url,
            "-o", str(self.dockge_dir / "compose.yaml")
        ])

        if not success:
            # Fallback: create compose.yaml manually
            console.print("[dim]Using fallback compose.yaml...[/dim]")
            compose_content = self._get_compose_yaml(port, stacks_path)
            if not write_file_sudo(str(self.dockge_dir / "compose.yaml"), compose_content):
                print_error("Failed to create compose.yaml")
                pause()
                return False

        # Start Dockge
        console.print("[dim]Starting Dockge...[/dim]")
        success, stdout, stderr = run_command([
            "docker", "compose", "-f", str(self.dockge_dir / "compose.yaml"),
            "up", "-d"
        ])

        if not success:
            print_error("Failed to start Dockge.")
            console.print(stderr)
            pause()
            return False

        print_success("Dockge installed and running!")
        console.print(f"\n[bold green]Access Dockge at: http://localhost:{port}[/bold green]")
        print_info("Create your admin account on first visit.")

        # Offer to open firewall port
        if confirm(f"\nOpen port {port} in firewall?"):
            from ..firewall import FirewallManager
            fw = FirewallManager()
            if fw.firewall_type.value != "none":
                run_sudo(["ufw", "allow", f"{port}/tcp"])
                print_success(f"Port {port} opened.")

        pause()
        return True

    def _get_compose_yaml(self, port: str, stacks_path: str) -> str:
        """Generate Dockge compose.yaml content.

        Args:
            port: Port to expose
            stacks_path: Path for stacks

        Returns:
            Compose file content
        """
        return f"""version: "3.8"
services:
  dockge:
    image: louislam/dockge:1
    container_name: dockge
    restart: unless-stopped
    ports:
      - "{port}:5001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - {stacks_path}:{stacks_path}
    environment:
      - DOCKGE_STACKS_DIR={stacks_path}
"""

    def start(self) -> bool:
        """Start Dockge.

        Returns:
            True on success, False on failure
        """
        if not self.is_installed():
            print_error("Dockge is not installed.")
            return False

        success, _, _ = run_command([
            "docker", "compose", "-f", str(self.dockge_dir / "compose.yaml"),
            "up", "-d"
        ])

        if success:
            print_success("Dockge started.")
        else:
            print_error("Failed to start Dockge.")

        return success

    def stop(self) -> bool:
        """Stop Dockge.

        Returns:
            True on success, False on failure
        """
        if not self.is_installed():
            print_error("Dockge is not installed.")
            return False

        success, _, _ = run_command([
            "docker", "compose", "-f", str(self.dockge_dir / "compose.yaml"),
            "down"
        ])

        if success:
            print_success("Dockge stopped.")
        else:
            print_error("Failed to stop Dockge.")

        return success

    def show_status(self) -> bool:
        """Show Dockge status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Dockge Status")

        if not self.is_installed():
            print_warning("Dockge is not installed.")
            if confirm("Install now?"):
                return self.install()
            pause()
            return False

        if self.is_running():
            print_success("Dockge is running.")

            # Get port from compose file
            try:
                compose_file = self.dockge_dir / "compose.yaml"
                content = compose_file.read_text()
                import re
                match = re.search(r'"(\d+):5001"', content)
                port = match.group(1) if match else "5001"
                console.print(f"\n[bold]Access URL:[/bold] http://localhost:{port}")
            except:
                pass
        else:
            print_warning("Dockge is not running.")
            if confirm("Start now?"):
                self.start()

        pause()
        return True

    def update(self) -> bool:
        """Update Dockge to latest version.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Update Dockge")

        if not self.is_installed():
            print_error("Dockge is not installed.")
            pause()
            return False

        console.print("[dim]Pulling latest image...[/dim]")
        run_command([
            "docker", "compose", "-f", str(self.dockge_dir / "compose.yaml"),
            "pull"
        ])

        console.print("[dim]Restarting Dockge...[/dim]")
        success, _, _ = run_command([
            "docker", "compose", "-f", str(self.dockge_dir / "compose.yaml"),
            "up", "-d"
        ])

        if success:
            print_success("Dockge updated!")
        else:
            print_error("Failed to update Dockge.")

        pause()
        return success

    def uninstall(self) -> bool:
        """Uninstall Dockge.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Uninstall Dockge")

        if not self.is_installed():
            print_warning("Dockge is not installed.")
            pause()
            return True

        print_warning("This will stop and remove Dockge.")
        print_info("Your stacks in /opt/stacks will NOT be deleted.")

        if not confirm("Proceed with uninstall?"):
            return False

        # Stop Dockge
        self.stop()

        # Remove container and image
        run_command(["docker", "rm", "dockge"])
        run_command(["docker", "rmi", "louislam/dockge:1"])

        # Remove Dockge directory
        if confirm("Remove Dockge data directory?"):
            run_sudo(["rm", "-rf", str(self.dockge_dir)])
            print_success("Dockge data removed.")

        print_success("Dockge uninstalled.")
        pause()
        return True
