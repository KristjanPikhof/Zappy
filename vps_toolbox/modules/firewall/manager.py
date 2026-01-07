"""Firewall management with UFW and firewalld support."""

from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ...utils.command import run_sudo, run_command, check_command_exists
from ...utils.ui import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    prompt,
    select_from_list,
    pause,
    clear_screen,
    print_header,
)
from ...utils.validators import validate_port


class FirewallType(Enum):
    """Supported firewall types."""
    UFW = "ufw"
    FIREWALLD = "firewalld"
    NONE = "none"


@dataclass
class FirewallRule:
    """Firewall rule information."""
    port: str
    protocol: str
    action: str  # allow/deny
    from_ip: Optional[str] = None


class FirewallManager:
    """Manages firewall rules (UFW or firewalld)."""

    def __init__(self):
        self._type: Optional[FirewallType] = None

    @property
    def firewall_type(self) -> FirewallType:
        """Detect and return the firewall type."""
        if self._type is not None:
            return self._type

        # Check for UFW first (common on Debian/Ubuntu)
        if check_command_exists("ufw"):
            # Check if UFW is active
            _, stdout, _ = run_command(["sudo", "ufw", "status"])
            if "active" in stdout.lower():
                self._type = FirewallType.UFW
                return self._type

        # Check for firewalld (common on RHEL/Fedora)
        if check_command_exists("firewall-cmd"):
            _, stdout, _ = run_command(["sudo", "firewall-cmd", "--state"])
            if "running" in stdout.lower():
                self._type = FirewallType.FIREWALLD
                return self._type

        # Default based on command availability
        if check_command_exists("ufw"):
            self._type = FirewallType.UFW
        elif check_command_exists("firewall-cmd"):
            self._type = FirewallType.FIREWALLD
        else:
            self._type = FirewallType.NONE

        return self._type

    def show_status(self) -> bool:
        """Show current firewall status.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Firewall Status")

        fw_type = self.firewall_type

        if fw_type == FirewallType.NONE:
            print_warning("No supported firewall found (UFW or firewalld).")
            print_info("Install UFW: sudo apt install ufw")
            print_info("Or firewalld: sudo dnf install firewalld")
            pause()
            return False

        console.print(f"[bold]Firewall Type:[/bold] {fw_type.value}")

        if fw_type == FirewallType.UFW:
            success, stdout, stderr = run_sudo(
                ["ufw", "status", "verbose"],
                show_command=False
            )
        else:
            success, stdout, stderr = run_sudo(
                ["firewall-cmd", "--list-all"],
                show_command=False
            )

        console.print(f"\n{stdout}")
        if stderr:
            console.print(f"[dim]{stderr}[/dim]")

        pause()
        return success

    def enable(self) -> bool:
        """Enable the firewall.

        Returns:
            True on success, False on failure
        """
        fw_type = self.firewall_type

        if fw_type == FirewallType.NONE:
            print_error("No supported firewall found.")
            return False

        print_warning("Enabling firewall. Make sure SSH port is open first!")

        if not confirm("Continue?"):
            return False

        if fw_type == FirewallType.UFW:
            # Allow SSH before enabling
            run_sudo(["ufw", "allow", "ssh"], show_command=False)
            success, _, _ = run_sudo(["ufw", "--force", "enable"])
        else:
            success, _, _ = run_sudo(["systemctl", "enable", "--now", "firewalld"])

        if success:
            print_success("Firewall enabled.")
        else:
            print_error("Failed to enable firewall.")

        return success

    def disable(self) -> bool:
        """Disable the firewall.

        Returns:
            True on success, False on failure
        """
        fw_type = self.firewall_type

        if fw_type == FirewallType.NONE:
            print_error("No supported firewall found.")
            return False

        print_warning("Disabling firewall will leave your system unprotected!")

        if not confirm("Are you sure?"):
            return False

        if fw_type == FirewallType.UFW:
            success, _, _ = run_sudo(["ufw", "disable"])
        else:
            success, _, _ = run_sudo(["systemctl", "disable", "--now", "firewalld"])

        if success:
            print_success("Firewall disabled.")
        else:
            print_error("Failed to disable firewall.")

        return success

    def open_port(self) -> bool:
        """Open a port in the firewall.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Open Port")

        fw_type = self.firewall_type
        if fw_type == FirewallType.NONE:
            print_error("No supported firewall found.")
            pause()
            return False

        port = prompt("Enter port number").strip()
        is_valid, error = validate_port(port)
        if not is_valid:
            print_error(error)
            pause()
            return False

        protocols = ["TCP only", "UDP only", "Both TCP and UDP"]
        choice = select_from_list(protocols, "Select protocol:")
        if choice is None:
            return False

        success = False

        if fw_type == FirewallType.UFW:
            if choice == 0:  # TCP
                success, _, _ = run_sudo(["ufw", "allow", f"{port}/tcp"])
            elif choice == 1:  # UDP
                success, _, _ = run_sudo(["ufw", "allow", f"{port}/udp"])
            else:  # Both
                success1, _, _ = run_sudo(["ufw", "allow", f"{port}/tcp"])
                success2, _, _ = run_sudo(["ufw", "allow", f"{port}/udp"])
                success = success1 and success2
        else:  # firewalld
            if choice == 0:  # TCP
                success, _, _ = run_sudo([
                    "firewall-cmd", "--add-port", f"{port}/tcp", "--permanent"
                ])
            elif choice == 1:  # UDP
                success, _, _ = run_sudo([
                    "firewall-cmd", "--add-port", f"{port}/udp", "--permanent"
                ])
            else:  # Both
                success1, _, _ = run_sudo([
                    "firewall-cmd", "--add-port", f"{port}/tcp", "--permanent"
                ])
                success2, _, _ = run_sudo([
                    "firewall-cmd", "--add-port", f"{port}/udp", "--permanent"
                ])
                success = success1 and success2

            if success:
                run_sudo(["firewall-cmd", "--reload"], show_command=False)

        if success:
            print_success(f"Port {port} opened.")
        else:
            print_error(f"Failed to open port {port}.")

        pause()
        return success

    def close_port(self) -> bool:
        """Close a port in the firewall.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Close Port")

        fw_type = self.firewall_type
        if fw_type == FirewallType.NONE:
            print_error("No supported firewall found.")
            pause()
            return False

        port = prompt("Enter port number to close").strip()
        is_valid, error = validate_port(port)
        if not is_valid:
            print_error(error)
            pause()
            return False

        protocols = ["TCP only", "UDP only", "Both TCP and UDP"]
        choice = select_from_list(protocols, "Select protocol:")
        if choice is None:
            return False

        success = False

        if fw_type == FirewallType.UFW:
            if choice == 0:  # TCP
                success, _, _ = run_sudo(["ufw", "delete", "allow", f"{port}/tcp"])
            elif choice == 1:  # UDP
                success, _, _ = run_sudo(["ufw", "delete", "allow", f"{port}/udp"])
            else:  # Both
                success1, _, _ = run_sudo(["ufw", "delete", "allow", f"{port}/tcp"])
                success2, _, _ = run_sudo(["ufw", "delete", "allow", f"{port}/udp"])
                success = success1 and success2
        else:  # firewalld
            if choice == 0:  # TCP
                success, _, _ = run_sudo([
                    "firewall-cmd", "--remove-port", f"{port}/tcp", "--permanent"
                ])
            elif choice == 1:  # UDP
                success, _, _ = run_sudo([
                    "firewall-cmd", "--remove-port", f"{port}/udp", "--permanent"
                ])
            else:  # Both
                success1, _, _ = run_sudo([
                    "firewall-cmd", "--remove-port", f"{port}/tcp", "--permanent"
                ])
                success2, _, _ = run_sudo([
                    "firewall-cmd", "--remove-port", f"{port}/udp", "--permanent"
                ])
                success = success1 and success2

            if success:
                run_sudo(["firewall-cmd", "--reload"], show_command=False)

        if success:
            print_success(f"Port {port} closed.")
        else:
            print_error(f"Failed to close port {port}.")

        pause()
        return success

    def allow_service(self) -> bool:
        """Allow a predefined service through the firewall.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Allow Service")

        fw_type = self.firewall_type
        if fw_type == FirewallType.NONE:
            print_error("No supported firewall found.")
            pause()
            return False

        services = [
            ("SSH", "ssh", 22),
            ("HTTP", "http", 80),
            ("HTTPS", "https", 443),
            ("MySQL", "mysql", 3306),
            ("PostgreSQL", "postgresql", 5432),
            ("Custom port...", None, None),
        ]

        items = [f"{s[0]} (port {s[2]})" if s[2] else s[0] for s in services]
        choice = select_from_list(items, "Select service:")
        if choice is None:
            return False

        if services[choice][1] is None:
            # Custom port
            return self.open_port()

        service_name = services[choice][1]

        if fw_type == FirewallType.UFW:
            success, _, _ = run_sudo(["ufw", "allow", service_name])
        else:
            success, _, _ = run_sudo([
                "firewall-cmd", "--add-service", service_name, "--permanent"
            ])
            if success:
                run_sudo(["firewall-cmd", "--reload"], show_command=False)

        if success:
            print_success(f"Service '{services[choice][0]}' allowed.")
        else:
            print_error(f"Failed to allow service.")

        pause()
        return success

    def list_rules(self) -> bool:
        """List all firewall rules.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Firewall Rules")

        fw_type = self.firewall_type
        if fw_type == FirewallType.NONE:
            print_error("No supported firewall found.")
            pause()
            return False

        if fw_type == FirewallType.UFW:
            success, stdout, _ = run_sudo(
                ["ufw", "status", "numbered"],
                show_command=False
            )
        else:
            console.print("[bold]Services:[/bold]")
            run_sudo(["firewall-cmd", "--list-services"], show_command=False)
            console.print("\n[bold]Ports:[/bold]")
            success, stdout, _ = run_sudo(
                ["firewall-cmd", "--list-ports"],
                show_command=False
            )

        console.print(stdout)
        pause()
        return success
