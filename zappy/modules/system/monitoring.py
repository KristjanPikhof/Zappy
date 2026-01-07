"""System monitoring utilities."""

from ...utils.command import run_sudo, run_command
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    select_from_list,
    pause,
    clear_screen,
    print_header,
)


class SystemMonitor:
    """System monitoring and status utilities."""

    def show_menu(self) -> bool:
        """Show monitoring menu.

        Returns:
            True on success
        """
        while True:
            clear_screen()
            print_header("System Monitoring")

            options = [
                "Resource Usage (CPU, Memory, Disk)",
                "Running Services",
                "Failed Services",
                "Network Connections",
                "Recent Logs",
            ]

            choice = select_from_list(options, "Select option:")
            if choice is None:
                return True

            if choice == 0:
                self.show_resources()
            elif choice == 1:
                self.show_services()
            elif choice == 2:
                self.show_failed_services()
            elif choice == 3:
                self.show_network()
            elif choice == 4:
                self.show_logs()

    def show_resources(self) -> bool:
        """Show system resource usage.

        Returns:
            True on success
        """
        clear_screen()
        print_header("System Resources")

        # CPU info
        console.print("[bold cyan]CPU Usage:[/bold cyan]")
        _, stdout, _ = run_command(["bash", "-c", "top -bn1 | head -5"])
        console.print(stdout)

        # Memory info
        console.print("\n[bold cyan]Memory Usage:[/bold cyan]")
        _, stdout, _ = run_command(["free", "-h"])
        console.print(stdout)

        # Disk usage
        console.print("\n[bold cyan]Disk Usage:[/bold cyan]")
        _, stdout, _ = run_command(["df", "-h", "/"])
        console.print(stdout)

        # Load average
        console.print("\n[bold cyan]Load Average:[/bold cyan]")
        _, stdout, _ = run_command(["uptime"])
        console.print(stdout)

        pause()
        return True

    def show_services(self) -> bool:
        """Show running services.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Running Services")

        _, stdout, _ = run_sudo([
            "systemctl", "list-units",
            "--type=service",
            "--state=running",
            "--no-pager"
        ], show_command=False)
        console.print(stdout)

        pause()
        return True

    def show_failed_services(self) -> bool:
        """Show failed services.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Failed Services")

        success, stdout, _ = run_sudo([
            "systemctl", "list-units",
            "--type=service",
            "--state=failed",
            "--no-pager"
        ], show_command=False)

        if "0 loaded units" in stdout or not stdout.strip():
            print_success("No failed services!")
        else:
            console.print(stdout)

        pause()
        return True

    def show_network(self) -> bool:
        """Show network connections.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Network Connections")

        # Listening ports
        console.print("[bold cyan]Listening Ports:[/bold cyan]")
        _, stdout, _ = run_sudo(["ss", "-tlnp"], show_command=False)
        console.print(stdout)

        # Active connections count
        console.print("\n[bold cyan]Connection Summary:[/bold cyan]")
        _, stdout, _ = run_command(["bash", "-c", "ss -s | head -10"])
        console.print(stdout)

        # IP addresses
        console.print("\n[bold cyan]IP Addresses:[/bold cyan]")
        _, stdout, _ = run_command(["hostname", "-I"])
        console.print(stdout)

        pause()
        return True

    def show_logs(self) -> bool:
        """Show recent system logs.

        Returns:
            True on success
        """
        clear_screen()
        print_header("Recent Logs")

        options = [
            "System logs (last 50 lines)",
            "Nginx logs (last 50 lines)",
            "SSH auth logs (last 50 lines)",
            "Kernel messages (dmesg)",
        ]

        choice = select_from_list(options, "Select log type:")
        if choice is None:
            return True

        clear_screen()

        if choice == 0:
            print_header("System Logs")
            _, stdout, _ = run_sudo(["journalctl", "-n", "50", "--no-pager"], show_command=False)
            console.print(stdout)

        elif choice == 1:
            print_header("Nginx Logs")
            console.print("[bold]Access Log:[/bold]")
            _, stdout, _ = run_sudo(["tail", "-20", "/var/log/nginx/access.log"], show_command=False)
            console.print(stdout if stdout else "[dim]No access log entries[/dim]")
            console.print("\n[bold]Error Log:[/bold]")
            _, stdout, _ = run_sudo(["tail", "-20", "/var/log/nginx/error.log"], show_command=False)
            console.print(stdout if stdout else "[dim]No error log entries[/dim]")

        elif choice == 2:
            print_header("SSH Auth Logs")
            # Try different log locations
            log_files = [
                "/var/log/auth.log",
                "/var/log/secure",
            ]
            found = False
            for log_file in log_files:
                success, stdout, _ = run_sudo(
                    ["tail", "-50", log_file],
                    show_command=False
                )
                if success and stdout:
                    console.print(stdout)
                    found = True
                    break
            if not found:
                _, stdout, _ = run_sudo(["journalctl", "-u", "sshd", "-n", "50", "--no-pager"], show_command=False)
                console.print(stdout)

        elif choice == 3:
            print_header("Kernel Messages")
            _, stdout, _ = run_sudo(["bash", "-c", "dmesg --time-format=reltime | tail -50"], show_command=False)
            console.print(stdout)

        pause()
        return True
