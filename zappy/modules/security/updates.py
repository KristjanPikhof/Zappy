"""Automatic security updates configuration."""

from ...utils.command import run_sudo, check_command_exists, write_file_sudo
from ...utils.distro import detect_distro, get_install_command, PackageManager
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


class AutoUpdatesManager:
    """Manages automatic security updates."""

    def setup(self) -> bool:
        """Set up automatic security updates.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Automatic Security Updates")

        distro = detect_distro()

        if distro.is_debian_based:
            return self._setup_debian()
        elif distro.is_rhel_based:
            return self._setup_rhel()
        elif distro.is_arch_based:
            print_warning("Arch Linux doesn't have official unattended upgrades.")
            print_info("Consider using 'pacman-contrib' with a timer for updates.")
            pause()
            return False
        elif distro.is_alpine:
            print_warning("Alpine Linux doesn't have unattended upgrades.")
            print_info("Consider using a cron job with 'apk upgrade'.")
            pause()
            return False
        else:
            print_error(f"Unsupported distribution: {distro.name}")
            pause()
            return False

    def _setup_debian(self) -> bool:
        """Set up unattended-upgrades on Debian/Ubuntu.

        Returns:
            True on success, False on failure
        """
        console.print("[bold]Setting up unattended-upgrades for Debian/Ubuntu[/bold]")

        # Install package
        console.print("\n[dim]Installing unattended-upgrades...[/dim]")
        success, _, _ = run_sudo(["apt", "install", "-y", "unattended-upgrades"])

        if not success:
            print_error("Failed to install unattended-upgrades.")
            pause()
            return False

        print_success("Package installed.")

        # Configure
        config = """// Zappy the VPS Toolbox - Unattended Upgrades Configuration
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

// Remove unused automatically installed kernel-related packages
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";

// Remove unused dependencies
Unattended-Upgrade::Remove-Unused-Dependencies "true";

// Automatically reboot if required
Unattended-Upgrade::Automatic-Reboot "false";

// If automatic reboot is enabled, reboot at this time
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
"""

        config_path = "/etc/apt/apt.conf.d/50unattended-upgrades"
        console.print("\n[dim]Configuring unattended-upgrades...[/dim]")

        if not write_file_sudo(config_path, config):
            print_warning("Using default configuration.")

        # Enable auto-updates
        auto_config = """APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
"""

        write_file_sudo("/etc/apt/apt.conf.d/20auto-upgrades", auto_config)

        # Enable service
        run_sudo(["systemctl", "enable", "unattended-upgrades"])
        run_sudo(["systemctl", "start", "unattended-upgrades"])

        print_success("Automatic security updates enabled.")
        print_info("Security updates will be installed automatically.")

        pause()
        return True

    def _setup_rhel(self) -> bool:
        """Set up dnf-automatic on RHEL/CentOS/Fedora.

        Returns:
            True on success, False on failure
        """
        console.print("[bold]Setting up dnf-automatic for RHEL/CentOS/Fedora[/bold]")

        # Install package
        console.print("\n[dim]Installing dnf-automatic...[/dim]")
        success, _, _ = run_sudo(["dnf", "install", "-y", "dnf-automatic"])

        if not success:
            print_error("Failed to install dnf-automatic.")
            pause()
            return False

        print_success("Package installed.")

        # Configure
        config = """# Zappy the VPS Toolbox - DNF Automatic Configuration
[commands]
upgrade_type = security
random_sleep = 0
download_updates = yes
apply_updates = yes

[emitters]
emit_via = stdio

[command]
upgrade_cmd = dnf
command_args = -y
"""

        config_path = "/etc/dnf/automatic.conf"
        console.print("\n[dim]Configuring dnf-automatic...[/dim]")

        if not write_file_sudo(config_path, config):
            print_warning("Using default configuration.")

        # Enable timer
        run_sudo(["systemctl", "enable", "dnf-automatic.timer"])
        run_sudo(["systemctl", "start", "dnf-automatic.timer"])

        print_success("Automatic security updates enabled.")
        print_info("Security updates will be checked daily.")

        pause()
        return True

    def show_status(self) -> bool:
        """Show auto-update status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Auto-Update Status")

        distro = detect_distro()

        if distro.is_debian_based:
            console.print("[bold]Unattended Upgrades Status:[/bold]")
            run_sudo(
                ["systemctl", "status", "unattended-upgrades", "--no-pager"],
                show_command=False
            )

            console.print("\n[bold]Last Update Log:[/bold]")
            run_sudo(
                ["tail", "-20", "/var/log/unattended-upgrades/unattended-upgrades.log"],
                show_command=False
            )

        elif distro.is_rhel_based:
            console.print("[bold]DNF Automatic Timer Status:[/bold]")
            run_sudo(
                ["systemctl", "status", "dnf-automatic.timer", "--no-pager"],
                show_command=False
            )

            console.print("\n[bold]Last Run:[/bold]")
            run_sudo(
                ["systemctl", "list-timers", "dnf-automatic.timer"],
                show_command=False
            )

        else:
            print_warning(f"Status check not available for {distro.name}")

        pause()
        return True

    def check_updates(self) -> bool:
        """Check for available security updates.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Check Security Updates")

        distro = detect_distro()

        if distro.is_debian_based:
            console.print("[dim]Checking for security updates...[/dim]\n")
            run_sudo(["apt", "update"], show_command=False)
            run_sudo(["apt", "list", "--upgradable"])

        elif distro.is_rhel_based:
            console.print("[dim]Checking for security updates...[/dim]\n")
            run_sudo(["dnf", "check-update", "--security"])

        else:
            print_warning(f"Update check not available for {distro.name}")

        pause()
        return True
