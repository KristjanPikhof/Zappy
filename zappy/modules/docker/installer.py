"""Docker installation and management."""

import os
from ...utils.command import run_sudo, run_command, check_command_exists, write_file_sudo
from ...utils.distro import detect_distro, PackageManager
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


class DockerInstaller:
    """Manages Docker installation."""

    def is_installed(self) -> bool:
        """Check if Docker is installed.

        Returns:
            True if installed, False otherwise
        """
        return check_command_exists("docker")

    def is_running(self) -> bool:
        """Check if Docker is running.

        Returns:
            True if running, False otherwise
        """
        # Try without sudo first
        success, _, _ = run_command(["docker", "info"])
        if success:
            return True

        # Try with sudo (needed before user logs out/in after install)
        success, _, _ = run_sudo(["docker", "info"], show_command=False)
        return success

    def install(self) -> bool:
        """Install Docker using official repository.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Install Docker")

        if self.is_installed():
            print_info("Docker is already installed.")
            self._show_version()
            pause()
            return True

        distro = detect_distro()
        console.print(f"Detected: {distro.name} ({distro.id})")

        if distro.is_debian_based:
            success = self._install_debian()
        elif distro.is_rhel_based:
            success = self._install_rhel()
        elif distro.is_arch_based:
            success = self._install_arch()
        else:
            print_error(f"Unsupported distribution: {distro.name}")
            print_info("Please install Docker manually from https://docs.docker.com/engine/install/")
            pause()
            return False

        if success:
            self._post_install()
            print_success("Docker installed successfully!")
            self._show_version()

        pause()
        return success

    def _install_debian(self) -> bool:
        """Install Docker on Debian/Ubuntu.

        Returns:
            True on success, False on failure
        """
        console.print("\n[bold]Installing Docker on Debian/Ubuntu...[/bold]\n")

        # Remove old versions
        console.print("[dim]Removing old Docker versions...[/dim]")
        run_sudo([
            "apt", "remove", "-y",
            "docker", "docker-engine", "docker.io", "containerd", "runc"
        ], show_command=False)

        # Install prerequisites
        console.print("[dim]Installing prerequisites...[/dim]")
        success, _, _ = run_sudo([
            "apt", "install", "-y",
            "ca-certificates", "curl", "gnupg", "lsb-release"
        ])
        if not success:
            print_error("Failed to install prerequisites.")
            return False

        # Add Docker GPG key
        console.print("[dim]Adding Docker GPG key...[/dim]")
        run_sudo(["mkdir", "-p", "/etc/apt/keyrings"])

        # Download and add key
        distro = detect_distro()
        if distro.id == "ubuntu":
            key_url = "https://download.docker.com/linux/ubuntu/gpg"
            repo_url = "https://download.docker.com/linux/ubuntu"
        else:
            key_url = "https://download.docker.com/linux/debian/gpg"
            repo_url = "https://download.docker.com/linux/debian"

        success, _, _ = run_command([
            "bash", "-c",
            f"curl -fsSL {key_url} | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
        ])

        run_sudo(["chmod", "a+r", "/etc/apt/keyrings/docker.gpg"])

        # Add repository
        console.print("[dim]Adding Docker repository...[/dim]")
        _, arch_out, _ = run_command(["dpkg", "--print-architecture"])
        arch = arch_out.strip()

        _, codename_out, _ = run_command(["bash", "-c", ". /etc/os-release && echo $VERSION_CODENAME"])
        codename = codename_out.strip()

        repo_line = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] {repo_url} {codename} stable"

        write_file_sudo("/etc/apt/sources.list.d/docker.list", repo_line + "\n")

        # Install Docker
        console.print("[dim]Installing Docker packages...[/dim]")
        run_sudo(["apt", "update"])
        success, _, _ = run_sudo([
            "apt", "install", "-y",
            "docker-ce", "docker-ce-cli", "containerd.io",
            "docker-buildx-plugin", "docker-compose-plugin"
        ])

        return success

    def _install_rhel(self) -> bool:
        """Install Docker on RHEL/CentOS/Fedora.

        Returns:
            True on success, False on failure
        """
        console.print("\n[bold]Installing Docker on RHEL/CentOS/Fedora...[/bold]\n")

        # Remove old versions
        console.print("[dim]Removing old Docker versions...[/dim]")
        run_sudo([
            "dnf", "remove", "-y",
            "docker", "docker-client", "docker-client-latest",
            "docker-common", "docker-latest", "docker-latest-logrotate",
            "docker-logrotate", "docker-engine"
        ], show_command=False)

        # Install prerequisites
        console.print("[dim]Installing prerequisites...[/dim]")
        run_sudo(["dnf", "install", "-y", "dnf-plugins-core"])

        # Add repository
        console.print("[dim]Adding Docker repository...[/dim]")
        distro = detect_distro()

        if distro.id == "fedora":
            repo_url = "https://download.docker.com/linux/fedora/docker-ce.repo"
        else:
            repo_url = "https://download.docker.com/linux/centos/docker-ce.repo"

        success, _, _ = run_sudo(["dnf", "config-manager", "--add-repo", repo_url])

        # Install Docker
        console.print("[dim]Installing Docker packages...[/dim]")
        success, _, _ = run_sudo([
            "dnf", "install", "-y",
            "docker-ce", "docker-ce-cli", "containerd.io",
            "docker-buildx-plugin", "docker-compose-plugin"
        ])

        return success

    def _install_arch(self) -> bool:
        """Install Docker on Arch Linux.

        Returns:
            True on success, False on failure
        """
        console.print("\n[bold]Installing Docker on Arch Linux...[/bold]\n")

        success, _, _ = run_sudo([
            "pacman", "-S", "--noconfirm",
            "docker", "docker-compose"
        ])

        return success

    def _post_install(self):
        """Perform post-installation steps."""
        console.print("\n[dim]Performing post-installation steps...[/dim]")

        # Start and enable Docker
        run_sudo(["systemctl", "enable", "docker"])
        run_sudo(["systemctl", "start", "docker"])

        # Add current user to docker group
        username = os.environ.get("SUDO_USER") or os.environ.get("USER")
        if username:
            console.print(f"[dim]Adding {username} to docker group...[/dim]")
            run_sudo(["usermod", "-aG", "docker", username])
            print_info(f"Log out and back in for group changes to take effect.")

    def _show_version(self):
        """Display Docker version."""
        console.print("\n[bold]Docker Version:[/bold]")
        run_command(["docker", "--version"])
        run_command(["docker", "compose", "version"])

    def show_status(self) -> bool:
        """Show Docker status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Docker Status")

        if not self.is_installed():
            print_warning("Docker is not installed.")
            if confirm("Install now?"):
                return self.install()
            pause()
            return False

        # Show version
        self._show_version()

        # Show service status
        console.print("\n[bold]Service Status:[/bold]")
        run_sudo(["systemctl", "status", "docker", "--no-pager", "-l"])

        # Show running containers
        console.print("\n[bold]Running Containers:[/bold]")
        run_command(["docker", "ps"])

        pause()
        return True

    def show_info(self) -> bool:
        """Show Docker system info.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Docker Info")

        if not self.is_installed():
            print_warning("Docker is not installed.")
            pause()
            return False

        run_command(["docker", "info"])
        pause()
        return True
