"""SSH configuration and hardening."""

import re
from pathlib import Path
from typing import Dict, Optional

from ...config import SSH_CONFIG_PATH, get_backup_path, ensure_backup_dir
from ...utils.command import run_sudo, read_file_sudo, write_file_sudo, backup_file
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
    display_status,
)
from ...utils.validators import validate_port


class SSHManager:
    """Manages SSH server configuration."""

    def __init__(self):
        self.config_path = SSH_CONFIG_PATH

    def get_current_settings(self) -> Dict[str, str]:
        """Get current SSH configuration settings.

        Returns:
            Dictionary of setting name to value
        """
        content = read_file_sudo(str(self.config_path))
        if not content:
            return {}

        settings = {}
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    settings[parts[0]] = parts[1]

        return settings

    def show_status(self) -> bool:
        """Show current SSH configuration status.

        Returns:
            True on success
        """
        clear_screen()
        print_header("SSH Configuration Status")

        settings = self.get_current_settings()

        # Check important settings
        port = settings.get("Port", "22")
        permit_root = settings.get("PermitRootLogin", "yes")
        password_auth = settings.get("PasswordAuthentication", "yes")
        pubkey_auth = settings.get("PubkeyAuthentication", "yes")

        items = [
            ("SSH Port", port, port != "22"),
            ("Root Login", permit_root, permit_root in ("no", "prohibit-password")),
            ("Password Auth", password_auth, password_auth == "no"),
            ("Public Key Auth", pubkey_auth, pubkey_auth == "yes"),
        ]

        display_status(items)

        console.print("\n[bold]Recommendations:[/bold]")
        if port == "22":
            print_warning("  Consider changing SSH port from default 22")
        if permit_root not in ("no", "prohibit-password"):
            print_warning("  Consider disabling root login")
        if password_auth != "no":
            print_warning("  Consider disabling password authentication")
        if pubkey_auth != "yes":
            print_warning("  Enable public key authentication")

        pause()
        return True

    def _modify_config(self, setting: str, value: str) -> bool:
        """Modify a single SSH configuration setting.

        Args:
            setting: Configuration directive name
            value: New value

        Returns:
            True on success, False on failure
        """
        content = read_file_sudo(str(self.config_path))
        if not content:
            print_error("Failed to read SSH configuration.")
            return False

        # Create backup
        ensure_backup_dir("ssh")
        backup_path = get_backup_path("ssh", "sshd_config")
        if not backup_file(str(self.config_path), str(backup_path)):
            print_error("Failed to create backup.")
            return False
        print_info(f"Backup created: {backup_path}")

        # Pattern to match the setting (commented or not)
        pattern = rf"^#?\s*{setting}\s+.*$"
        new_line = f"{setting} {value}"

        if re.search(pattern, content, re.MULTILINE):
            # Replace existing line
            new_content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
        else:
            # Add new line at end
            new_content = content.rstrip() + f"\n{new_line}\n"

        if not write_file_sudo(str(self.config_path), new_content):
            print_error("Failed to write configuration.")
            return False

        # Test configuration
        console.print("\n[dim]Testing SSH configuration...[/dim]")
        success, _, stderr = run_sudo(["sshd", "-t"], show_command=False)

        if not success:
            print_error("Configuration test failed!")
            console.print(f"[red]{stderr}[/red]")
            if confirm("Restore backup?", default=True):
                backup_file(str(backup_path), str(self.config_path))
                print_success("Backup restored.")
            return False

        print_success("Configuration syntax OK.")
        return True

    def change_port(self) -> bool:
        """Change the SSH port.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Change SSH Port")

        current = self.get_current_settings().get("Port", "22")
        console.print(f"Current port: {current}")

        new_port = prompt("Enter new SSH port (1024-65535 recommended)").strip()

        is_valid, error = validate_port(new_port)
        if not is_valid:
            print_error(error)
            pause()
            return False

        if int(new_port) < 1024:
            print_warning("Ports below 1024 are privileged. Using a higher port is recommended.")
            if not confirm("Continue anyway?"):
                return False

        print_warning(f"Changing SSH port to {new_port}")
        print_warning("Make sure to:")
        print_info("  1. Open the new port in firewall BEFORE restart")
        print_info("  2. Test connection on new port before closing old port")
        print_info("  3. Update any SSH clients to use the new port")

        if not confirm("\nProceed with port change?"):
            return False

        if self._modify_config("Port", new_port):
            print_success(f"SSH port changed to {new_port}")

            if confirm("Restart SSH service now?"):
                success, _, _ = run_sudo(["systemctl", "restart", "sshd"])
                if success:
                    print_success("SSH service restarted.")
                    print_warning(f"Connect with: ssh -p {new_port} user@host")
                else:
                    print_error("Failed to restart SSH service.")

        pause()
        return True

    def disable_root_login(self) -> bool:
        """Disable root login via SSH.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Disable Root Login")

        current = self.get_current_settings().get("PermitRootLogin", "yes")
        console.print(f"Current setting: {current}")

        options = [
            "no - Completely disable root login (recommended)",
            "prohibit-password - Allow only with SSH key",
            "yes - Allow root login (not recommended)",
        ]

        choice = select_from_list(options, "Select option:")
        if choice is None:
            return False

        values = ["no", "prohibit-password", "yes"]
        value = values[choice]

        print_warning("Make sure you have another user with sudo access!")

        if not confirm("Proceed?"):
            return False

        if self._modify_config("PermitRootLogin", value):
            print_success(f"Root login set to: {value}")

            if confirm("Restart SSH service now?"):
                success, _, _ = run_sudo(["systemctl", "restart", "sshd"])
                if success:
                    print_success("SSH service restarted.")

        pause()
        return True

    def disable_password_auth(self) -> bool:
        """Disable password authentication (key-only).

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Configure Password Authentication")

        current = self.get_current_settings().get("PasswordAuthentication", "yes")
        console.print(f"Current setting: {current}")

        print_warning("Before disabling password authentication:")
        print_info("  1. Ensure you have SSH keys set up")
        print_info("  2. Test key-based login works")
        print_info("  3. Have console access as backup")

        options = [
            "no - Disable password auth (key-only, recommended)",
            "yes - Enable password auth",
        ]

        choice = select_from_list(options, "Select option:")
        if choice is None:
            return False

        values = ["no", "yes"]
        value = values[choice]

        if value == "no":
            print_warning("You will only be able to login with SSH keys!")
            if not confirm("Are you sure?"):
                return False

        if self._modify_config("PasswordAuthentication", value):
            print_success(f"Password authentication set to: {value}")

            if confirm("Restart SSH service now?"):
                success, _, _ = run_sudo(["systemctl", "restart", "sshd"])
                if success:
                    print_success("SSH service restarted.")

        pause()
        return True

    def harden_all(self) -> bool:
        """Apply recommended SSH hardening settings.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("SSH Hardening Wizard")

        print_info("This wizard will apply recommended SSH security settings:")
        console.print("  • Disable root login")
        console.print("  • Enable public key authentication")
        console.print("  • Set stricter permissions")
        console.print()

        print_warning("Before proceeding, ensure:")
        print_info("  1. You have another user with sudo access")
        print_info("  2. Your SSH key is installed")
        print_info("  3. You have console access as backup")

        if not confirm("\nProceed with hardening?"):
            return False

        # Backup first
        ensure_backup_dir("ssh")
        backup_path = get_backup_path("ssh", "sshd_config")
        if not backup_file(str(self.config_path), str(backup_path)):
            print_error("Failed to create backup.")
            pause()
            return False
        print_success(f"Backup created: {backup_path}")

        content = read_file_sudo(str(self.config_path))
        if not content:
            print_error("Failed to read configuration.")
            pause()
            return False

        # Settings to apply
        hardening_settings = {
            "PermitRootLogin": "prohibit-password",
            "PubkeyAuthentication": "yes",
            "MaxAuthTries": "3",
            "ClientAliveInterval": "300",
            "ClientAliveCountMax": "2",
        }

        new_content = content
        for setting, value in hardening_settings.items():
            pattern = rf"^#?\s*{setting}\s+.*$"
            new_line = f"{setting} {value}"

            if re.search(pattern, new_content, re.MULTILINE):
                new_content = re.sub(pattern, new_line, new_content, flags=re.MULTILINE)
            else:
                new_content = new_content.rstrip() + f"\n{new_line}\n"

        if not write_file_sudo(str(self.config_path), new_content):
            print_error("Failed to write configuration.")
            pause()
            return False

        # Test configuration
        success, _, stderr = run_sudo(["sshd", "-t"], show_command=False)
        if not success:
            print_error("Configuration test failed!")
            backup_file(str(backup_path), str(self.config_path))
            print_success("Backup restored.")
            pause()
            return False

        print_success("SSH hardening applied:")
        for setting, value in hardening_settings.items():
            console.print(f"  • {setting} = {value}")

        if confirm("\nRestart SSH service now?"):
            success, _, _ = run_sudo(["systemctl", "restart", "sshd"])
            if success:
                print_success("SSH service restarted.")

        pause()
        return True
