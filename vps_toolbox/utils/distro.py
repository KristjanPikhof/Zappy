"""Linux distribution detection and package manager utilities."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from pathlib import Path


class PackageManager(Enum):
    """Supported package managers."""
    APT = "apt"
    DNF = "dnf"
    YUM = "yum"
    PACMAN = "pacman"
    APK = "apk"
    ZYPPER = "zypper"
    UNKNOWN = "unknown"


@dataclass
class DistroInfo:
    """Linux distribution information."""
    id: str
    name: str
    version: str
    id_like: List[str]
    package_manager: PackageManager

    @property
    def is_debian_based(self) -> bool:
        return self.id in ("debian", "ubuntu") or "debian" in self.id_like

    @property
    def is_rhel_based(self) -> bool:
        return self.id in ("rhel", "centos", "fedora", "rocky", "alma") or any(
            x in self.id_like for x in ("rhel", "fedora", "centos")
        )

    @property
    def is_arch_based(self) -> bool:
        return self.id == "arch" or "arch" in self.id_like

    @property
    def is_alpine(self) -> bool:
        return self.id == "alpine"

    @property
    def is_suse_based(self) -> bool:
        return self.id in ("opensuse", "sles") or "suse" in self.id_like


def detect_distro() -> DistroInfo:
    """Detect the current Linux distribution.

    Returns:
        DistroInfo object with distribution details
    """
    os_release = Path("/etc/os-release")

    distro_id = "unknown"
    distro_name = "Unknown"
    distro_version = ""
    id_like: List[str] = []

    if os_release.exists():
        with open(os_release) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ID="):
                    distro_id = line.split("=", 1)[1].strip('"').lower()
                elif line.startswith("NAME="):
                    distro_name = line.split("=", 1)[1].strip('"')
                elif line.startswith("VERSION_ID="):
                    distro_version = line.split("=", 1)[1].strip('"')
                elif line.startswith("ID_LIKE="):
                    id_like = line.split("=", 1)[1].strip('"').lower().split()

    # Determine package manager
    package_manager = _detect_package_manager(distro_id, id_like)

    return DistroInfo(
        id=distro_id,
        name=distro_name,
        version=distro_version,
        id_like=id_like,
        package_manager=package_manager,
    )


def _detect_package_manager(distro_id: str, id_like: List[str]) -> PackageManager:
    """Detect the package manager for the given distribution.

    Args:
        distro_id: Distribution ID
        id_like: List of similar distribution IDs

    Returns:
        PackageManager enum value
    """
    # Check by distro ID first
    if distro_id in ("debian", "ubuntu", "linuxmint", "pop", "elementary", "zorin"):
        return PackageManager.APT
    elif distro_id in ("fedora",):
        return PackageManager.DNF
    elif distro_id in ("rhel", "centos", "rocky", "alma"):
        # RHEL 8+ and derivatives use dnf
        return PackageManager.DNF
    elif distro_id == "arch":
        return PackageManager.PACMAN
    elif distro_id == "alpine":
        return PackageManager.APK
    elif distro_id in ("opensuse", "opensuse-leap", "opensuse-tumbleweed", "sles"):
        return PackageManager.ZYPPER

    # Check by id_like
    if "debian" in id_like:
        return PackageManager.APT
    elif "fedora" in id_like or "rhel" in id_like:
        return PackageManager.DNF
    elif "arch" in id_like:
        return PackageManager.PACMAN
    elif "suse" in id_like:
        return PackageManager.ZYPPER

    # Check if commands exist
    from .command import check_command_exists

    if check_command_exists("apt"):
        return PackageManager.APT
    elif check_command_exists("dnf"):
        return PackageManager.DNF
    elif check_command_exists("yum"):
        return PackageManager.YUM
    elif check_command_exists("pacman"):
        return PackageManager.PACMAN
    elif check_command_exists("apk"):
        return PackageManager.APK
    elif check_command_exists("zypper"):
        return PackageManager.ZYPPER

    return PackageManager.UNKNOWN


def get_package_manager() -> PackageManager:
    """Get the current system's package manager.

    Returns:
        PackageManager enum value
    """
    return detect_distro().package_manager


def get_install_command(packages: List[str], package_manager: Optional[PackageManager] = None) -> List[str]:
    """Get the install command for packages.

    Args:
        packages: List of package names
        package_manager: Package manager to use (auto-detected if None)

    Returns:
        Command as list of strings
    """
    if package_manager is None:
        package_manager = get_package_manager()

    commands = {
        PackageManager.APT: ["apt", "install", "-y"],
        PackageManager.DNF: ["dnf", "install", "-y"],
        PackageManager.YUM: ["yum", "install", "-y"],
        PackageManager.PACMAN: ["pacman", "-S", "--noconfirm"],
        PackageManager.APK: ["apk", "add"],
        PackageManager.ZYPPER: ["zypper", "install", "-y"],
    }

    base_cmd = commands.get(package_manager, ["echo", "Unknown package manager"])
    return base_cmd + packages


def get_update_command(package_manager: Optional[PackageManager] = None) -> List[str]:
    """Get the package list update command.

    Args:
        package_manager: Package manager to use (auto-detected if None)

    Returns:
        Command as list of strings
    """
    if package_manager is None:
        package_manager = get_package_manager()

    commands = {
        PackageManager.APT: ["apt", "update"],
        PackageManager.DNF: ["dnf", "check-update"],
        PackageManager.YUM: ["yum", "check-update"],
        PackageManager.PACMAN: ["pacman", "-Sy"],
        PackageManager.APK: ["apk", "update"],
        PackageManager.ZYPPER: ["zypper", "refresh"],
    }

    return commands.get(package_manager, ["echo", "Unknown package manager"])
