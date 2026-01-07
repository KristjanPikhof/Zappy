"""Certbot SSL certificate management."""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ...config import CERTBOT_EMAIL_FILE
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
    display_table,
)
from ...utils.validators import validate_email
from .manager import NginxManager


@dataclass
class CertificateInfo:
    """Information about an SSL certificate."""
    name: str
    domains: List[str]
    expiry: str
    path: str


class CertbotManager:
    """Manages SSL certificates via Certbot."""

    def __init__(self):
        self.nginx_manager = NginxManager()
        self._email: Optional[str] = None

    @property
    def email(self) -> Optional[str]:
        """Get the stored Certbot email."""
        if self._email:
            return self._email

        email_file = Path(CERTBOT_EMAIL_FILE)
        if email_file.exists():
            self._email = email_file.read_text().strip()
            return self._email

        return None

    @email.setter
    def email(self, value: str):
        """Store the Certbot email."""
        self._email = value
        email_file = Path(CERTBOT_EMAIL_FILE)
        email_file.parent.mkdir(parents=True, exist_ok=True)
        email_file.write_text(value)

    def is_installed(self) -> bool:
        """Check if Certbot is installed.

        Returns:
            True if installed, False otherwise
        """
        return check_command_exists("certbot")

    def _get_email(self) -> Optional[str]:
        """Get or prompt for Certbot email.

        Returns:
            Email address or None if cancelled
        """
        if self.email:
            if confirm(f"Use existing email ({self.email})?", default=True):
                return self.email

        while True:
            email = prompt("Enter email for certificate notifications").strip()
            is_valid, error = validate_email(email)

            if is_valid:
                self.email = email
                return email

            print_error(error)
            if not confirm("Try again?"):
                return None

    def add_https(self) -> bool:
        """Add HTTPS to a domain using Certbot.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Add HTTPS Certificate")

        if not self.is_installed():
            print_error("Certbot is not installed.")
            print_info("Install it with: sudo apt install certbot python3-certbot-nginx")
            pause()
            return False

        # Get domains
        domains = self.nginx_manager.get_domains()
        enabled = [d for d in domains if d.is_enabled and not d.has_ssl]

        if not enabled:
            print_warning("No enabled domains without SSL found.")
            print_info("Enable a domain first, or all domains already have SSL.")
            pause()
            return False

        items = [d.name for d in enabled]
        choice = select_from_list(items, "Select domain to secure:")
        if choice is None:
            return False

        domain = enabled[choice]

        # Get email
        email = self._get_email()
        if not email:
            print_warning("Email is required for certificate notifications.")
            pause()
            return False

        # Confirm
        console.print(f"\n[bold]Certificate Details:[/bold]")
        console.print(f"  Domain: {domain.name}")
        console.print(f"  Email: {email}")

        print_warning("\nEnsure DNS is pointing to this server and ports 80/443 are open!")

        if not confirm("\nProceed with certificate request?", default=True):
            return False

        # Run Certbot
        console.print("\n[dim]Requesting certificate...[/dim]\n")

        cmd = [
            "certbot",
            "--nginx",
            "-d", domain.name,
            "--email", email,
            "--agree-tos",
            "--non-interactive",
            "--redirect",  # Auto redirect HTTP to HTTPS
        ]

        success, stdout, stderr = run_sudo(cmd, show_command=True)

        if success:
            print_success(f"HTTPS enabled for {domain.name}!")
            print_info("Certificate will auto-renew via systemd timer.")
        else:
            print_error("Certificate request failed.")
            if "Challenge failed" in (stderr or ""):
                print_warning("DNS may not be pointing to this server.")
            console.print(stderr)

        pause()
        return success

    def list_certificates(self) -> List[CertificateInfo]:
        """List all SSL certificates.

        Returns:
            List of CertificateInfo objects
        """
        clear_screen()
        print_header("SSL Certificates")

        if not self.is_installed():
            print_error("Certbot is not installed.")
            pause()
            return []

        success, stdout, stderr = run_sudo(
            ["certbot", "certificates"],
            show_command=False
        )

        if not success:
            print_error("Failed to list certificates.")
            pause()
            return []

        # Parse output
        certs = []
        current_cert = {}

        for line in stdout.split("\n"):
            line = line.strip()

            if line.startswith("Certificate Name:"):
                if current_cert:
                    certs.append(CertificateInfo(
                        name=current_cert.get("name", ""),
                        domains=current_cert.get("domains", []),
                        expiry=current_cert.get("expiry", ""),
                        path=current_cert.get("path", ""),
                    ))
                current_cert = {"name": line.split(":", 1)[1].strip()}

            elif line.startswith("Domains:"):
                current_cert["domains"] = line.split(":", 1)[1].strip().split()

            elif line.startswith("Expiry Date:"):
                current_cert["expiry"] = line.split(":", 1)[1].strip()

            elif line.startswith("Certificate Path:"):
                current_cert["path"] = line.split(":", 1)[1].strip()

        if current_cert:
            certs.append(CertificateInfo(
                name=current_cert.get("name", ""),
                domains=current_cert.get("domains", []),
                expiry=current_cert.get("expiry", ""),
                path=current_cert.get("path", ""),
            ))

        if not certs:
            print_warning("No certificates found.")
        else:
            for cert in certs:
                console.print(f"\n[bold cyan]{cert.name}[/bold cyan]")
                console.print(f"  Domains: {', '.join(cert.domains)}")
                console.print(f"  Expires: {cert.expiry}")
                console.print(f"  Path: {cert.path}")

        pause()
        return certs

    def renew_certificate(self) -> bool:
        """Renew SSL certificates.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Renew Certificates")

        if not self.is_installed():
            print_error("Certbot is not installed.")
            pause()
            return False

        options = [
            "Renew all certificates (recommended)",
            "Renew specific certificate",
            "Dry run (test renewal)",
        ]

        choice = select_from_list(options, "Select renewal option:")
        if choice is None:
            return False

        if choice == 0:
            # Renew all
            console.print("\n[dim]Renewing all certificates...[/dim]\n")
            success, stdout, stderr = run_sudo(["certbot", "renew"])

        elif choice == 1:
            # Renew specific
            certs = self._get_certificate_names()
            if not certs:
                print_warning("No certificates found to renew.")
                pause()
                return False

            cert_choice = select_from_list(certs, "Select certificate to renew:")
            if cert_choice is None:
                return False

            console.print(f"\n[dim]Renewing {certs[cert_choice]}...[/dim]\n")
            success, stdout, stderr = run_sudo([
                "certbot", "renew",
                "--cert-name", certs[cert_choice]
            ])

        else:
            # Dry run
            console.print("\n[dim]Testing certificate renewal (dry run)...[/dim]\n")
            success, stdout, stderr = run_sudo(["certbot", "renew", "--dry-run"])

        if success:
            print_success("Certificate renewal completed.")
        else:
            print_error("Certificate renewal failed.")

        console.print(stdout)
        if stderr:
            console.print(f"[dim]{stderr}[/dim]")

        pause()
        return success

    def delete_certificate(self) -> bool:
        """Delete an SSL certificate.

        Returns:
            True on success, False on failure
        """
        clear_screen()
        print_header("Delete Certificate")

        if not self.is_installed():
            print_error("Certbot is not installed.")
            pause()
            return False

        certs = self._get_certificate_names()
        if not certs:
            print_warning("No certificates found to delete.")
            pause()
            return False

        choice = select_from_list(certs, "Select certificate to delete:")
        if choice is None:
            return False

        cert_name = certs[choice]

        print_warning(f"This will permanently delete the certificate for '{cert_name}'!")
        print_warning("You should also remove the SSL configuration from nginx.")

        if not confirm("Are you sure?"):
            return False

        console.print(f"\n[dim]Deleting certificate {cert_name}...[/dim]\n")

        success, stdout, stderr = run_sudo([
            "certbot", "delete",
            "--cert-name", cert_name,
            "--non-interactive"
        ])

        if success:
            print_success(f"Certificate '{cert_name}' deleted.")
            print_warning("Remember to update your nginx configuration!")
        else:
            print_error("Failed to delete certificate.")
            console.print(stderr)

        pause()
        return success

    def _get_certificate_names(self) -> List[str]:
        """Get list of certificate names.

        Returns:
            List of certificate names
        """
        success, stdout, stderr = run_sudo(
            ["certbot", "certificates"],
            show_command=False
        )

        if not success:
            return []

        names = []
        for line in stdout.split("\n"):
            if line.strip().startswith("Certificate Name:"):
                names.append(line.split(":", 1)[1].strip())

        return names

    def check_renewal_timer(self) -> bool:
        """Check the status of the certbot renewal timer.

        Returns:
            True if timer is active, False otherwise
        """
        clear_screen()
        print_header("Renewal Timer Status")

        success, stdout, stderr = run_sudo(
            ["systemctl", "status", "certbot.timer", "--no-pager"],
            show_command=False
        )

        console.print(stdout or stderr)
        pause()
        return success
