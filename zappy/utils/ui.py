"""Terminal UI utilities using rich library."""

import os
import sys
from typing import List, Optional, Callable, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

# Global console instance
console = Console()


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str, subtitle: str = ""):
    """Print a styled header.

    Args:
        title: Main title text
        subtitle: Optional subtitle
    """
    text = Text()
    text.append(title, style="bold cyan")
    if subtitle:
        text.append(f"\n{subtitle}", style="dim")

    console.print(Panel(text, box=box.ROUNDED, border_style="cyan"))


def print_success(message: str):
    """Print a success message.

    Args:
        message: Message to display
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print an error message.

    Args:
        message: Message to display
    """
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    """Print a warning message.

    Args:
        message: Message to display
    """
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str):
    """Print an info message.

    Args:
        message: Message to display
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def confirm(message: str, default: bool = False) -> bool:
    """Ask for confirmation.

    Args:
        message: Question to ask
        default: Default value if user just presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    return Confirm.ask(message, default=default)


def prompt(message: str, default: str = "", password: bool = False) -> str:
    """Prompt for text input.

    Args:
        message: Prompt message
        default: Default value
        password: Whether to hide input

    Returns:
        User input string
    """
    return Prompt.ask(message, default=default, password=password)


def select_from_list(
    items: List[str],
    title: str = "Select an option",
    allow_back: bool = True,
    show_numbers: bool = True,
) -> Optional[int]:
    """Display a selection list and get user choice.

    Args:
        items: List of items to choose from
        title: Title for the selection
        allow_back: Whether to show a "Back" option
        show_numbers: Whether to show numbers for items

    Returns:
        Selected index (0-based) or None if back/cancelled
    """
    console.print(f"\n[bold]{title}[/bold]")

    for i, item in enumerate(items, 1):
        if show_numbers:
            console.print(f"  [cyan]{i}.[/cyan] {item}")
        else:
            console.print(f"  • {item}")

    if allow_back:
        console.print(f"  [dim]b. Back[/dim]")

    while True:
        choice = prompt("\nEnter choice").strip().lower()

        if allow_back and choice == "b":
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return idx
            print_error("Invalid choice. Please try again.")
        except ValueError:
            print_error("Please enter a number.")


def create_menu(
    title: str,
    options: List[tuple],
    subtitle: str = "",
) -> Optional[Any]:
    """Create and display an interactive menu.

    Args:
        title: Menu title
        options: List of (label, handler) tuples. Handler can be a function or submenu.
        subtitle: Optional subtitle

    Returns:
        Result from selected handler or None if quit/back
    """
    clear_screen()
    print_header(title, subtitle)

    items = [opt[0] for opt in options]
    choice = select_from_list(items, "Choose an option:", allow_back=True)

    if choice is None:
        return None

    handler = options[choice][1]
    if callable(handler):
        return handler()
    return handler


def display_table(
    title: str,
    columns: List[str],
    rows: List[List[str]],
    show_header: bool = True,
):
    """Display data in a table format.

    Args:
        title: Table title
        columns: Column headers
        rows: List of row data
        show_header: Whether to show column headers
    """
    table = Table(title=title, box=box.ROUNDED, show_header=show_header)

    for col in columns:
        table.add_column(col, style="cyan")

    for row in rows:
        table.add_row(*row)

    console.print(table)


def pause(message: str = "Press Enter to continue..."):
    """Pause and wait for user input.

    Args:
        message: Message to display
    """
    console.input(f"\n[dim]{message}[/dim]")


def display_status(items: List[tuple]):
    """Display a status list with colored indicators.

    Args:
        items: List of (label, status, is_ok) tuples
    """
    for label, status, is_ok in items:
        color = "green" if is_ok else "red"
        indicator = "●" if is_ok else "○"
        console.print(f"  [{color}]{indicator}[/{color}] {label}: {status}")
