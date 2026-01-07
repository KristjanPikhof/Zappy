"""Nginx domain management."""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ...config import (
    NGINX_SITES_AVAILABLE,
    NGINX_SITES_ENABLED,
    get_backup_path,
    ensure_backup_dir,
)
from ...utils.command import run_sudo, write_file_sudo, read_file_sudo, backup_file
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
from ...utils.validators import validate_domain, normalize_proxy_url
from .templates import get_template, TEMPLATE_TYPES


@dataclass
class DomainInfo:
    """Information about a configured domain."""
    name: str
    config_path: str
    is_enabled: bool
    has_ssl: bool = False


class NginxManager:
    """Manages nginx domain configurations."""

    def __init__(self):
        self.sites_available = Path(NGINX_SITES_AVAILABLE)
        self.sites_enabled = Path(NGINX_SITES_ENABLED)

    def get_domains(self) -> List[DomainInfo]:
        """Get all configured domains.

        Returns:
            List of DomainInfo objects
        """
        domains = []

        if not self.sites_available.is_dir():
            print_error(f"Nginx sites-available directory not found: {self.sites_available}")
            return domains

        # Get enabled domains (symlinks in sites-enabled)
        enabled_names = set()
        if self.sites_enabled.is_dir():
            for item in self.sites_enabled.iterdir():
                if item.is_symlink():
                    target = item.resolve()
                    if str(target).startswith(str(self.sites_available)):
                        enabled_names.add(item.name)

        # Get all available domains
        for config_file in sorted(self.sites_available.iterdir()):
            if config_file.is_file():
                # Check if SSL is configured (simple check for listen 443)
                has_ssl = False
                try:
                    content = config_file.read_text()
                    has_ssl = "listen 443" in content or "ssl_certificate" in content
                except:
                    pass

                domains.append(DomainInfo(
                    name=config_file.name,
                    config_path=str(config_file),
                    is_enabled=config_file.name in enabled_names,
                    has_ssl=has_ssl,
                ))

        return domains

    def list_domains(self) -> List[DomainInfo]:
        """List all domains with their status.

        Returns:
            List of DomainInfo objects
        """
        clear_screen()
        print_header("Configured Domains")

        domains = self.get_domains()

        if not domains:
            print_warning("No domain configurations found.")
            pause()
            return []

        console.print()
        for i, domain in enumerate(domains, 1):
            status_parts = []
            if domain.is_enabled:
                status_parts.append("[green]Enabled[/green]")
            else:
                status_parts.append("[yellow]Disabled[/yellow]")

            if domain.has_ssl:
                status_parts.append("[cyan]SSL[/cyan]")

            status = " | ".join(status_parts)
            console.print(f"  {i}. {domain.name} ({status})")

        pause()
        return domains

    def add_domain(self) -> bool:
        """Add a new domain configuration.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Add New Domain")

        # Get domain name
        server_name = prompt("Enter domain name (e.g., example.com)").strip()

        is_valid, error = validate_domain(server_name)
        if not is_valid:
            print_error(error)
            pause()
            return False

        config_path = self.sites_available / server_name

        if config_path.exists():
            print_warning(f"Configuration for '{server_name}' already exists.")
            if not confirm("Overwrite existing configuration?"):
                return False

        # Select template type
        console.print("\n[bold]Select configuration template:[/bold]")
        template_items = list(TEMPLATE_TYPES.values())
        template_keys = list(TEMPLATE_TYPES.keys())

        choice = select_from_list(template_items, "Template type:", allow_back=True)
        if choice is None:
            return False

        template_type = template_keys[choice]

        # Get template-specific options
        proxy_pass = None
        root_path = None
        redirect_url = None

        if template_type in ("proxy", "proxy-ws"):
            proxy_url = prompt("Enter backend URL (e.g., localhost:3000)").strip()
            if not proxy_url:
                print_error("Backend URL is required.")
                pause()
                return False
            proxy_pass = normalize_proxy_url(proxy_url)

        elif template_type in ("static", "php"):
            default_root = f"/var/www/{server_name}"
            root_path = prompt(f"Enter root path", default=default_root).strip()

        elif template_type == "redirect":
            redirect_url = prompt("Enter redirect target URL").strip()
            if not redirect_url:
                print_error("Redirect URL is required.")
                pause()
                return False

        # Generate configuration
        config_content = get_template(
            template_type=template_type,
            server_name=server_name,
            proxy_pass=proxy_pass,
            root_path=root_path,
            redirect_url=redirect_url,
        )

        # Write configuration
        console.print(f"\n[dim]Creating configuration at {config_path}...[/dim]")

        if not write_file_sudo(str(config_path), config_content):
            print_error("Failed to create configuration file.")
            pause()
            return False

        print_success(f"Configuration created: {config_path}")

        # Test configuration
        if not self.test_config():
            print_error("Nginx configuration test failed!")
            pause()
            return False

        # Offer to enable
        if confirm("Enable this domain now?", default=True):
            self.enable_domain(server_name)

        pause()
        return True

    def enable_domain(self, domain_name: Optional[str] = None) -> bool:
        """Enable a domain configuration.

        Args:
            domain_name: Domain to enable, or None to select interactively

        Returns:
            True on success, False on failure
        """
        if domain_name is None:
            clear_screen()
            print_header("Enable Domain")

            domains = self.get_domains()
            disabled = [d for d in domains if not d.is_enabled]

            if not disabled:
                print_warning("No disabled domains to enable.")
                pause()
                return False

            items = [d.name for d in disabled]
            choice = select_from_list(items, "Select domain to enable:")
            if choice is None:
                return False

            domain_name = disabled[choice].name

        source = self.sites_available / domain_name
        dest = self.sites_enabled / domain_name

        if dest.exists() or dest.is_symlink():
            print_warning(f"Domain '{domain_name}' is already enabled.")
            return False

        success, _, _ = run_sudo(["ln", "-s", str(source), str(dest)])
        if not success:
            print_error(f"Failed to enable domain '{domain_name}'.")
            return False

        if not self.test_config():
            run_sudo(["rm", str(dest)], show_command=False)
            print_error("Configuration test failed. Reverted changes.")
            return False

        if not self.reload():
            return False

        print_success(f"Domain '{domain_name}' enabled.")
        return True

    def disable_domain(self, domain_name: Optional[str] = None) -> bool:
        """Disable a domain configuration (remove symlink only).

        Args:
            domain_name: Domain to disable, or None to select interactively

        Returns:
            True on success, False on failure
        """
        if domain_name is None:
            clear_screen()
            print_header("Disable Domain")

            domains = self.get_domains()
            enabled = [d for d in domains if d.is_enabled]

            if not enabled:
                print_warning("No enabled domains to disable.")
                pause()
                return False

            items = [d.name for d in enabled]
            choice = select_from_list(items, "Select domain to disable:")
            if choice is None:
                return False

            domain_name = enabled[choice].name

        symlink = self.sites_enabled / domain_name

        if not symlink.is_symlink():
            print_warning(f"Domain '{domain_name}' is not enabled.")
            return False

        success, _, _ = run_sudo(["rm", str(symlink)])
        if not success:
            print_error(f"Failed to disable domain '{domain_name}'.")
            return False

        if not self.test_config():
            print_error("Configuration test failed after disabling.")
            return False

        if not self.reload():
            return False

        print_success(f"Domain '{domain_name}' disabled.")
        pause()
        return True

    def delete_domain(self) -> bool:
        """Delete a domain configuration completely.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Delete Domain")

        domains = self.get_domains()
        if not domains:
            print_warning("No domains to delete.")
            pause()
            return False

        items = [f"{d.name} ({'Enabled' if d.is_enabled else 'Disabled'})" for d in domains]
        choice = select_from_list(items, "Select domain to delete:")
        if choice is None:
            return False

        domain = domains[choice]

        print_warning(f"This will permanently delete '{domain.name}'!")
        if not confirm("Are you sure?"):
            return False

        # Remove symlink if enabled
        symlink = self.sites_enabled / domain.name
        if symlink.is_symlink():
            run_sudo(["rm", str(symlink)], show_command=False)

        # Backup before deleting
        ensure_backup_dir("nginx")
        backup_path = get_backup_path("nginx", domain.name)
        backup_file(domain.config_path, str(backup_path))
        print_info(f"Backup created: {backup_path}")

        # Delete config file
        success, _, _ = run_sudo(["rm", domain.config_path])
        if not success:
            print_error(f"Failed to delete configuration.")
            pause()
            return False

        if not self.test_config():
            print_warning("Configuration test failed after deletion.")

        self.reload()
        print_success(f"Domain '{domain.name}' deleted.")
        pause()
        return True

    def view_config(self) -> bool:
        """View a domain's configuration.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("View Configuration")

        domains = self.get_domains()
        if not domains:
            print_warning("No domains configured.")
            pause()
            return False

        items = [d.name for d in domains]
        choice = select_from_list(items, "Select domain to view:")
        if choice is None:
            return False

        domain = domains[choice]
        content = read_file_sudo(domain.config_path)

        if content:
            clear_screen()
            print_header(f"Configuration: {domain.name}")
            console.print(f"\n[dim]{domain.config_path}[/dim]\n")
            console.print(content)
        else:
            print_error("Failed to read configuration file.")

        pause()
        return True

    def edit_config(self) -> bool:
        """Edit a domain's configuration in an editor.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Edit Configuration")

        domains = self.get_domains()
        if not domains:
            print_warning("No domains configured.")
            pause()
            return False

        items = [d.name for d in domains]
        choice = select_from_list(items, "Select domain to edit:")
        if choice is None:
            return False

        domain = domains[choice]

        # Create backup first
        ensure_backup_dir("nginx")
        backup_path = get_backup_path("nginx", domain.name)
        backup_file(domain.config_path, str(backup_path))
        print_info(f"Backup created: {backup_path}")

        # Find available editor
        editors = ["micro", "nano", "vim", "vi"]
        editor = None
        for ed in editors:
            from ...utils.command import check_command_exists
            if check_command_exists(ed):
                editor = ed
                break

        if not editor:
            print_error("No text editor found. Please install micro, nano, or vim.")
            pause()
            return False

        console.print(f"\n[dim]Opening {domain.config_path} with {editor}...[/dim]")
        console.print("[dim]Save and exit the editor when done.[/dim]\n")

        # Run editor with sudo
        import subprocess
        subprocess.run(["sudo", editor, domain.config_path])

        # Test config after editing
        if not self.test_config():
            print_error("Configuration test failed!")
            if confirm("Restore backup?", default=True):
                backup_file(str(backup_path), domain.config_path)
                print_success("Backup restored.")
        else:
            if confirm("Reload nginx?", default=True):
                self.reload()

        pause()
        return True

    def test_config(self) -> bool:
        """Test nginx configuration syntax.

        Returns:
            True if config is valid, False otherwise
        """
        console.print("\n[dim]Testing nginx configuration...[/dim]")
        success, stdout, stderr = run_sudo(["nginx", "-t"], show_command=False)

        if success:
            print_success("Configuration syntax OK.")
        else:
            print_error("Configuration test failed.")
            if stderr:
                console.print(f"[red]{stderr}[/red]")

        return success

    def reload(self) -> bool:
        """Reload nginx service.

        Returns:
            True on success, False on failure
        """
        console.print("\n[dim]Reloading nginx...[/dim]")
        success, _, _ = run_sudo(["systemctl", "reload", "nginx"])

        if success:
            print_success("Nginx reloaded successfully.")
        else:
            print_error("Failed to reload nginx.")

        return success

    def status(self) -> bool:
        """Show nginx service status.

        Returns:
            True (always)
        """
        clear_screen()
        print_header("Nginx Status")

        success, stdout, stderr = run_sudo(
            ["systemctl", "status", "nginx", "--no-pager"],
            show_command=False
        )

        console.print(stdout or stderr)
        pause()
        return True
