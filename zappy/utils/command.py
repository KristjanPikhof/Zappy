"""Command execution utilities with sudo support."""

import subprocess
import shutil
from typing import Optional, Tuple, List, Union
from .ui import console, print_error


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    return shutil.which(command) is not None


def run_command(
    command: Union[str, List[str]],
    capture_output: bool = True,
    check: bool = False,
    timeout: Optional[int] = None,
    input_text: Optional[str] = None,
) -> Tuple[int, str, str]:
    """Run a command and return result.

    Args:
        command: Command to run (string or list)
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise on non-zero exit
        timeout: Command timeout in seconds
        input_text: Text to pass to stdin

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    if isinstance(command, str):
        command = command.split()

    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout,
            input=input_text,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {command[0]}"
    except Exception as e:
        return -1, "", str(e)


def run_sudo(
    command: Union[str, List[str]],
    capture_output: bool = True,
    check: bool = False,
    timeout: Optional[int] = None,
    input_text: Optional[str] = None,
    show_command: bool = True,
) -> Tuple[bool, str, str]:
    """Run a command with sudo.

    Args:
        command: Command to run (string or list)
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise on non-zero exit
        timeout: Command timeout in seconds
        input_text: Text to pass to stdin
        show_command: Whether to display the command being run

    Returns:
        Tuple of (success, stdout, stderr)
    """
    if isinstance(command, str):
        command = command.split()

    full_command = ["sudo"] + command

    if show_command:
        console.print(f"[dim]Running: {' '.join(full_command)}[/dim]")

    returncode, stdout, stderr = run_command(
        full_command,
        capture_output=capture_output,
        check=check,
        timeout=timeout,
        input_text=input_text,
    )

    success = returncode == 0

    if not success and stderr:
        print_error(f"Command failed: {stderr.strip()}")

    return success, stdout, stderr


def write_file_sudo(path: str, content: str) -> bool:
    """Write content to a file using sudo tee.

    Args:
        path: File path to write to
        content: Content to write

    Returns:
        True on success, False on failure
    """
    try:
        process = subprocess.Popen(
            ["sudo", "tee", path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        _, stderr = process.communicate(input=content)

        if process.returncode != 0:
            print_error(f"Failed to write file: {stderr}")
            return False
        return True
    except Exception as e:
        print_error(f"Failed to write file: {e}")
        return False


def read_file_sudo(path: str) -> Optional[str]:
    """Read a file using sudo.

    Args:
        path: File path to read

    Returns:
        File content or None on failure
    """
    success, stdout, stderr = run_sudo(["cat", path], show_command=False)
    if success:
        return stdout
    return None


def backup_file(source: str, dest: str) -> bool:
    """Create a backup of a file using sudo.

    Args:
        source: Source file path
        dest: Destination backup path

    Returns:
        True on success, False on failure
    """
    success, _, _ = run_sudo(["cp", source, dest], show_command=False)
    return success


def verify_sudo() -> bool:
    """Verify that sudo is available and user has permissions.

    Returns:
        True if sudo is available, False otherwise
    """
    returncode, _, _ = run_command(["sudo", "-v"])
    return returncode == 0
