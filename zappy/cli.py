"""Main CLI interface for Zappy the VPS Toolbox."""

from .utils.ui import (
    console,
    clear_screen,
    print_header,
    print_error,
    select_from_list,
    pause,
)
from .utils.command import verify_sudo

# Import managers
from .modules.nginx import NginxManager, CertbotManager
from .modules.firewall import FirewallManager
from .modules.security import SSHManager, Fail2banManager, AutoUpdatesManager
from .modules.docker import DockerInstaller, DockgeManager
from .modules.system import PackagesManager, ShellSetup, AiTermyInstaller, SystemMonitor


class VPSToolbox:
    """Main CLI application."""

    VERSION = "1.0.0"

    def __init__(self):
        self.nginx = NginxManager()
        self.certbot = CertbotManager()
        self.firewall = FirewallManager()
        self.ssh = SSHManager()
        self.fail2ban = Fail2banManager()
        self.updates = AutoUpdatesManager()
        self.docker = DockerInstaller()
        self.dockge = DockgeManager()
        self.packages = PackagesManager()
        self.shell = ShellSetup()
        self.aitermy = AiTermyInstaller()
        self.monitor = SystemMonitor()

    def run(self):
        """Run the main application loop."""
        if not verify_sudo():
            print_error("This tool requires sudo privileges.")
            print_error("Please run with sudo or configure sudo permissions.")
            return

        while True:
            if not self.main_menu():
                break

    def main_menu(self) -> bool:
        """Display the main menu.

        Returns:
            True to continue, False to exit
        """
        clear_screen()
        print_header(f"Zappy the VPS Toolbox v{self.VERSION}", "Comprehensive VPS Management")

        options = [
            "Nginx Management",
            "Firewall Management",
            "Security Hardening",
            "Docker Setup",
            "System Utilities",
        ]

        choice = select_from_list(options, "Choose a category:")

        if choice is None:
            return False

        if choice == 0:
            self.nginx_menu()
        elif choice == 1:
            self.firewall_menu()
        elif choice == 2:
            self.security_menu()
        elif choice == 3:
            self.docker_menu()
        elif choice == 4:
            self.system_menu()

        return True

    def nginx_menu(self):
        """Display Nginx management menu."""
        while True:
            clear_screen()
            print_header("Nginx Management")

            options = [
                "List domains",
                "Add domain",
                "Enable domain",
                "Disable domain",
                "Delete domain",
                "View/Edit config",
                "SSL Certificates",
                "Reload nginx",
                "Nginx status",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.nginx.list_domains()
            elif choice == 1:
                self.nginx.add_domain()
            elif choice == 2:
                self.nginx.enable_domain()
            elif choice == 3:
                self.nginx.disable_domain()
            elif choice == 4:
                self.nginx.delete_domain()
            elif choice == 5:
                self.nginx_config_menu()
            elif choice == 6:
                self.ssl_menu()
            elif choice == 7:
                self.nginx.reload()
            elif choice == 8:
                self.nginx.status()

    def nginx_config_menu(self):
        """Display Nginx config submenu."""
        clear_screen()
        print_header("View/Edit Configuration")

        options = [
            "View configuration",
            "Edit configuration",
        ]

        choice = select_from_list(options, "Select action:")

        if choice == 0:
            self.nginx.view_config()
        elif choice == 1:
            self.nginx.edit_config()

    def ssl_menu(self):
        """Display SSL certificates menu."""
        while True:
            clear_screen()
            print_header("SSL Certificates")

            options = [
                "Add HTTPS to domain",
                "List certificates",
                "Renew certificates",
                "Delete certificate",
                "Check renewal timer",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.certbot.add_https()
            elif choice == 1:
                self.certbot.list_certificates()
            elif choice == 2:
                self.certbot.renew_certificate()
            elif choice == 3:
                self.certbot.delete_certificate()
            elif choice == 4:
                self.certbot.check_renewal_timer()

    def firewall_menu(self):
        """Display firewall management menu."""
        while True:
            clear_screen()
            print_header("Firewall Management")

            options = [
                "Show status",
                "Open port",
                "Close port",
                "Allow service",
                "List rules",
                "Enable firewall",
                "Disable firewall",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.firewall.show_status()
            elif choice == 1:
                self.firewall.open_port()
            elif choice == 2:
                self.firewall.close_port()
            elif choice == 3:
                self.firewall.allow_service()
            elif choice == 4:
                self.firewall.list_rules()
            elif choice == 5:
                self.firewall.enable()
                pause()
            elif choice == 6:
                self.firewall.disable()
                pause()

    def security_menu(self):
        """Display security hardening menu."""
        while True:
            clear_screen()
            print_header("Security Hardening")

            options = [
                "SSH Configuration",
                "Fail2ban Setup",
                "Automatic Updates",
            ]

            choice = select_from_list(options, "Select category:")

            if choice is None:
                return

            if choice == 0:
                self.ssh_menu()
            elif choice == 1:
                self.fail2ban_menu()
            elif choice == 2:
                self.updates_menu()

    def ssh_menu(self):
        """Display SSH configuration menu."""
        while True:
            clear_screen()
            print_header("SSH Configuration")

            options = [
                "Show current status",
                "Change SSH port",
                "Configure root login",
                "Configure password authentication",
                "Apply recommended hardening",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.ssh.show_status()
            elif choice == 1:
                self.ssh.change_port()
            elif choice == 2:
                self.ssh.disable_root_login()
            elif choice == 3:
                self.ssh.disable_password_auth()
            elif choice == 4:
                self.ssh.harden_all()

    def fail2ban_menu(self):
        """Display Fail2ban menu."""
        while True:
            clear_screen()
            print_header("Fail2ban")

            options = [
                "Show status",
                "Install/Configure",
                "Show banned IPs",
                "Unban IP",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.fail2ban.show_status()
            elif choice == 1:
                self.fail2ban.install()
            elif choice == 2:
                self.fail2ban.show_banned()
            elif choice == 3:
                self.fail2ban.unban_ip()

    def updates_menu(self):
        """Display auto-updates menu."""
        while True:
            clear_screen()
            print_header("Automatic Security Updates")

            options = [
                "Show status",
                "Setup auto-updates",
                "Check for updates",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.updates.show_status()
            elif choice == 1:
                self.updates.setup()
            elif choice == 2:
                self.updates.check_updates()

    def docker_menu(self):
        """Display Docker setup menu."""
        while True:
            clear_screen()
            print_header("Docker Setup")

            options = [
                "Docker status",
                "Install Docker",
                "Docker info",
                "Dockge status",
                "Install Dockge",
                "Update Dockge",
                "Uninstall Dockge",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.docker.show_status()
            elif choice == 1:
                self.docker.install()
            elif choice == 2:
                self.docker.show_info()
            elif choice == 3:
                self.dockge.show_status()
            elif choice == 4:
                self.dockge.install()
            elif choice == 5:
                self.dockge.update()
            elif choice == 6:
                self.dockge.uninstall()

    def system_menu(self):
        """Display system utilities menu."""
        while True:
            clear_screen()
            print_header("System Utilities")

            options = [
                "Install common tools",
                "Show installed tools",
                "Setup zsh + oh-my-zsh",
                "Shell status",
                "Install AiTermy",
                "Update AiTermy",
                "Uninstall AiTermy",
                "AiTermy status",
                "System monitoring",
            ]

            choice = select_from_list(options, "Select action:")

            if choice is None:
                return

            if choice == 0:
                self.packages.install_menu()
            elif choice == 1:
                self.packages.show_installed()
            elif choice == 2:
                self.shell.setup()
            elif choice == 3:
                self.shell.show_status()
            elif choice == 4:
                self.aitermy.install()
            elif choice == 5:
                self.aitermy.update()
            elif choice == 6:
                self.aitermy.uninstall()
            elif choice == 7:
                self.aitermy.show_status()
            elif choice == 8:
                self.monitor.show_menu()


def main():
    """Entry point for the CLI."""
    try:
        app = VPSToolbox()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Exiting...[/dim]")
    except Exception as e:
        print_error(f"An error occurred: {e}")
        raise
