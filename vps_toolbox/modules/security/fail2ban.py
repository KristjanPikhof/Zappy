"""Fail2ban installation and management."""

from typing import Optional
from pathlib import Path

from ...utils.command import run_sudo, check_command_exists, write_file_sudo
from ...utils.distro import get_package_manager, get_install_command, PackageManager
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


class Fail2banManager:
    """Manages fail2ban installation and configuration."""

    def __init__(self):
        self.config_dir = Path("/etc/fail2ban")
        self.jail_local = self.config_dir / "jail.local"

    def is_installed(self) -> bool:
        """Check if fail2ban is installed.

        Returns:
            True if installed, False otherwise
        """
        return check_command_exists("fail2ban-client")

    def is_running(self) -> bool:
        """Check if fail2ban is running.

        Returns:
            True if running, False otherwise
        """
        success, _, _ = run_sudo(
            ["systemctl", "is-active", "fail2ban"],
            show_command=False
        )
        return success

    def install(self) -> bool:
        """Install fail2ban.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Install Fail2ban")

        if self.is_installed():
            print_info("Fail2ban is already installed.")
            if not confirm("Reconfigure?"):
                pause()
                return True

        pm = get_package_manager()

        # Package name varies by distro
        package = "fail2ban"
        if pm == PackageManager.APK:
            print_error("Fail2ban is not available on Alpine Linux.")
            print_info("Consider using sshguard instead.")
            pause()
            return False

        console.print("\n[dim]Installing fail2ban...[/dim]")

        install_cmd = get_install_command([package], pm)
        success, _, _ = run_sudo(install_cmd)

        if not success:
            print_error("Failed to install fail2ban.")
            pause()
            return False

        print_success("Fail2ban installed.")

        # Configure and enable
        if confirm("Configure fail2ban with recommended settings?", default=True):
            self._configure_default()

        # Enable and start
        console.print("\n[dim]Enabling fail2ban service...[/dim]")
        run_sudo(["systemctl", "enable", "fail2ban"])
        run_sudo(["systemctl", "start", "fail2ban"])

        print_success("Fail2ban is now active.")
        pause()
        return True

    def _configure_default(self) -> bool:
        """Apply default fail2ban configuration.

        Returns:
            True on success, False on failure
        """
        console.print("\n[dim]Applying default configuration...[/dim]")

        config = """# Zappy the VPS Toolbox - Fail2ban Configuration
[DEFAULT]
# Ban hosts for 1 hour
bantime = 1h

# Find time window (10 minutes)
findtime = 10m

# Max retries before ban
maxretry = 5

# Ignore local IPs
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h

# For RHEL/CentOS style logs
[sshd-systemd]
enabled = true
backend = systemd
filter = sshd
maxretry = 3
bantime = 1h
"""

        if write_file_sudo(str(self.jail_local), config):
            print_success("Configuration applied.")
            return True

        print_error("Failed to write configuration.")
        return False

    def show_status(self) -> bool:
        """Show fail2ban status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Fail2ban Status")

        if not self.is_installed():
            print_warning("Fail2ban is not installed.")
            if confirm("Install now?"):
                return self.install()
            pause()
            return False

        # Show service status
        console.print("[bold]Service Status:[/bold]")
        run_sudo(["systemctl", "status", "fail2ban", "--no-pager", "-l"])

        # Show jail status
        console.print("\n[bold]Active Jails:[/bold]")
        success, stdout, _ = run_sudo(
            ["fail2ban-client", "status"],
            show_command=False
        )
        console.print(stdout)

        pause()
        return True

    def show_banned(self) -> bool:
        """Show currently banned IPs.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Banned IPs")

        if not self.is_installed() or not self.is_running():
            print_warning("Fail2ban is not running.")
            pause()
            return False

        # Get list of jails
        success, stdout, _ = run_sudo(
            ["fail2ban-client", "status"],
            show_command=False
        )

        if not success:
            print_error("Failed to get jail list.")
            pause()
            return False

        # Extract jail names
        jails = []
        for line in stdout.split("\n"):
            if "Jail list:" in line:
                jail_str = line.split(":", 1)[1].strip()
                jails = [j.strip() for j in jail_str.split(",") if j.strip()]

        if not jails:
            print_info("No active jails.")
            pause()
            return True

        # Show banned IPs for each jail
        for jail in jails:
            console.print(f"\n[bold cyan]{jail}:[/bold cyan]")
            success, stdout, _ = run_sudo(
                ["fail2ban-client", "status", jail],
                show_command=False
            )

            for line in stdout.split("\n"):
                if "Banned IP" in line or "Currently banned" in line:
                    console.print(f"  {line.strip()}")

        pause()
        return True

    def unban_ip(self) -> bool:
        """Unban an IP address.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Unban IP Address")

        if not self.is_installed() or not self.is_running():
            print_warning("Fail2ban is not running.")
            pause()
            return False

        ip = prompt("Enter IP address to unban").strip()
        if not ip:
            print_error("IP address is required.")
            pause()
            return False

        # Try to unban from all jails
        success, stdout, _ = run_sudo(
            ["fail2ban-client", "unban", ip],
            show_command=True
        )

        if success:
            print_success(f"IP {ip} unbanned.")
        else:
            print_warning(f"IP {ip} may not be banned or error occurred.")

        pause()
        return success
