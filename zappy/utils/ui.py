"""Terminal UI utilities using rich library."""

import os
import sys
from typing import List, Optional, Callable, Any, Dict, Set, Tuple
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


def parse_multi_select_indices(
    raw_input: str,
    item_count: int,
    special_keywords: Optional[Dict[str, List[int]]] = None,
) -> Tuple[Optional[List[int]], Optional[str]]:
    """Parse multi-select input into deterministic, deduplicated indices.

    Supports comma-separated numbers and ranges (e.g. ``2,3,5,10`` and ``4-7``),
    plus optional caller-provided keywords such as ``all/*`` or ``missing/m``.

    Args:
        raw_input: Raw user input string
        item_count: Number of selectable items
        special_keywords: Optional keyword map to indices (0-based)

    Returns:
        A tuple of ``(indices, error_message)``.
        - ``indices`` is a list of deduplicated indices in menu order when valid
        - ``error_message`` is set when parsing fails
    """
    value = (raw_input or "").strip().lower()
    if not value:
        return None, "Input is empty. Enter numbers, ranges, or a supported keyword."

    keyword_map = {k.lower(): v for k, v in (special_keywords or {}).items()}
    if value in keyword_map:
        selected: Set[int] = set()
        for idx in keyword_map[value]:
            if not 0 <= idx < item_count:
                return None, (
                    f"Keyword '{value}' contains out-of-range value: {idx + 1}. "
                    f"Valid range is 1-{item_count}."
                )
            selected.add(idx)
        return [i for i in range(item_count) if i in selected], None

    selected: Set[int] = set()
    tokens = [token.strip() for token in value.split(",")]

    for token in tokens:
        if not token:
            return None, "Malformed token: empty value between commas."

        if "-" in token:
            parts = [part.strip() for part in token.split("-")]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return None, f"Malformed token '{token}'. Expected range like '4-7'."

            try:
                start = int(parts[0])
                end = int(parts[1])
            except ValueError:
                return None, f"Malformed token '{token}'. Range values must be numbers."

            if start > end:
                return None, (
                    f"Invalid range '{token}'. Range start must be less than or equal "
                    "to range end."
                )

            if start < 1 or end > item_count:
                return None, (
                    f"Out-of-range value in '{token}'. Valid range is 1-{item_count}."
                )

            for val in range(start, end + 1):
                selected.add(val - 1)
            continue

        try:
            num = int(token)
        except ValueError:
            return None, f"Malformed token '{token}'. Expected number or range like '4-7'."

        if not 1 <= num <= item_count:
            return None, (
                f"Out-of-range value '{num}'. Valid range is 1-{item_count}."
            )

        selected.add(num - 1)

    return [i for i in range(item_count) if i in selected], None


def multi_select_from_list(
    items: List[str],
    title: str = "Select one or more options",
    allow_back: bool = True,
    back_value: str = "b",
    special_keywords: Optional[Dict[str, List[int]]] = None,
    show_numbers: bool = True,
) -> Optional[List[int]]:
    """Display options and read multi-selection input.

    This helper keeps existing ``create_menu`` / ``select_from_list`` behavior intact
    while offering reusable multi-select input handling with optional back/cancel.

    Args:
        items: List of items to choose from
        title: Title for the selection section
        allow_back: Whether to show and accept a back/cancel option
        back_value: Back/cancel input value (default: ``b``)
        special_keywords: Optional map of input keywords to index lists (0-based)
        show_numbers: Whether to show numbers for items

    Returns:
        List of selected indices (0-based) in deterministic menu order,
        or ``None`` when back/cancel is selected.
    """
    console.print(f"\n[bold]{title}[/bold]")

    for i, item in enumerate(items, 1):
        if show_numbers:
            console.print(f"  [cyan]{i}.[/cyan] {item}")
        else:
            console.print(f"  • {item}")

    hints: List[str] = ["comma-separated numbers (e.g. 1,3,5)", "ranges (e.g. 4-7)"]
    if special_keywords:
        hints.append("keywords: " + ", ".join(sorted(special_keywords.keys())))
    console.print(f"  [dim]Hint: {'; '.join(hints)}[/dim]")

    normalized_back = (back_value or "b").strip().lower()
    if allow_back:
        console.print(f"  [dim]{normalized_back}. Back/Cancel[/dim]")

    while True:
        choice = prompt("\nEnter choices").strip().lower()
        if allow_back and choice == normalized_back:
            return None

        indices, error = parse_multi_select_indices(
            choice,
            len(items),
            special_keywords=special_keywords,
        )
        if error:
            print_error(error)
            print_info(
                f"Try again with numbers 1-{len(items)}, ranges like 2-4, "
                "or supported keywords."
            )
            continue

        return indices


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
