"""Rich console display formatting for dictionary output."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from wut.core.models import Bookmark, Meaning, Word


class WordFormatter:
    """Formatter for displaying dictionary data using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize formatter with optional console.

        Args:
            console: Rich console instance. Creates new one if not provided.
        """
        self._console = console or Console()

    @property
    def console(self) -> Console:
        """Get the console instance."""
        return self._console

    def display_word(self, word: Word) -> None:
        """Display a word with all its meanings.

        Args:
            word: Word object to display.
        """
        # Header panel with word and phonetic
        header_text = Text()
        header_text.append(text=word.word.title(), style="bold cyan")
        if word.ipa:
            header_text.append(text=f"  {word.ipa}", style="italic dim")

        header = Panel(
            renderable=header_text,
            title="[bold green]Word",
            border_style="green",
            padding=(0, 2),
        )
        self._console.print(header)
        self._console.print()

        # Meanings table
        table = Table(
            title="Definitions",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            padding=(0, 1),
        )
        table.add_column(header="Part of Speech", style="yellow bold", width=15)
        table.add_column(header="Definition", style="white")
        table.add_column(header="Example", style="dim italic", width=30)

        for meaning in word.meanings:
            self._add_meaning_rows(table=table, meaning=meaning)

        self._console.print(table)
        self._console.print()

        # Synonyms and antonyms
        self._display_synonyms_antonyms(word=word)

    def _add_meaning_rows(self, table: Table, meaning: Meaning) -> None:
        """Add rows for a meaning to the table."""
        for i, definition in enumerate(meaning.definitions):
            pos = meaning.part_of_speech if i == 0 else ""
            example = definition.example or "—"
            table.add_row(pos, definition.text, example)

    def _display_synonyms_antonyms(self, word: Word) -> None:
        """Display synonyms and antonyms table."""
        synonyms = word.all_synonyms
        antonyms = word.all_antonyms

        if not synonyms and not antonyms:
            return

        table = Table(
            title="Synonyms & Antonyms",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column(header="Synonyms", style="green")
        table.add_column(header="Antonyms", style="red")

        # Display up to 10 of each
        max_items = 10
        syn_text = ", ".join(synonyms[:max_items]) if synonyms else "—"
        ant_text = ", ".join(antonyms[:max_items]) if antonyms else "—"

        if len(synonyms) > max_items:
            syn_text += f" (+{len(synonyms) - max_items} more)"
        if len(antonyms) > max_items:
            ant_text += f" (+{len(antonyms) - max_items} more)"

        table.add_row(syn_text, ant_text)
        self._console.print(table)

    def display_bookmark(self, bookmark: Bookmark) -> None:
        """Display a single bookmark.

        Args:
            bookmark: Bookmark to display.
        """
        header_text = Text()
        header_text.append(text=bookmark.word.title(), style="bold cyan")
        if bookmark.phonetic:
            header_text.append(text=f"  {bookmark.phonetic}", style="italic dim")
        if bookmark.part_of_speech:
            header_text.append(text=f"  [{bookmark.part_of_speech}]", style="yellow")

        panel_content = Text()
        panel_content.append(text=bookmark.definition)

        if bookmark.example:
            panel_content.append(text="\n\n")
            panel_content.append(text="Example: ", style="bold")
            panel_content.append(text=f'"{bookmark.example}"', style="italic")

        panel = Panel(
            renderable=panel_content,
            title=header_text,
            border_style="green",
            padding=(1, 2),
        )
        self._console.print(panel)

        # Show synonyms/antonyms if present
        if bookmark.synonyms or bookmark.antonyms:
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            table.add_column(header="Label", style="bold")
            table.add_column(header="Value")

            if bookmark.synonyms:
                table.add_row("Synonyms:", bookmark.synonyms)
            if bookmark.antonyms:
                table.add_row("Antonyms:", bookmark.antonyms)

            self._console.print(table)

    def display_bookmark_list(
        self,
        bookmarks: list[Bookmark],
        *,
        show_count: bool = True,
    ) -> None:
        """Display a list of bookmarks as a table.

        Args:
            bookmarks: List of bookmarks to display.
            show_count: Whether to show total count.
        """
        if not bookmarks:
            self._console.print("[yellow]No bookmarks found.[/yellow]")
            return

        table = Table(
            title="Bookmarked Words",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column(header="#", style="dim", width=4)
        table.add_column(header="Word", style="cyan bold")
        table.add_column(header="Part of Speech", style="yellow", width=12)
        table.add_column(header="Definition", style="white", max_width=50)
        table.add_column(header="Added", style="dim", width=12)

        for i, bookmark in enumerate(bookmarks, 1):
            # Truncate definition if too long
            definition = bookmark.definition
            if len(definition) > 47:
                definition = definition[:47] + "..."

            table.add_row(
                str(i),
                bookmark.word,
                bookmark.part_of_speech,
                definition,
                bookmark.added_at.strftime("%Y-%m-%d"),
            )

        self._console.print(table)

        if show_count:
            self._console.print(f"\n[dim]Total: {len(bookmarks)} bookmark(s)[/dim]")

    def display_error(self, message: str) -> None:
        """Display an error message.

        Args:
            message: Error message to display.
        """
        self._console.print(f"[bold red]Error:[/bold red] {message}")

    def display_success(self, message: str) -> None:
        """Display a success message.

        Args:
            message: Success message to display.
        """
        self._console.print(f"[bold green]✓[/bold green] {message}")

    def display_warning(self, message: str) -> None:
        """Display a warning message.

        Args:
            message: Warning message to display.
        """
        self._console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    def display_info(self, message: str) -> None:
        """Display an info message.

        Args:
            message: Info message to display.
        """
        self._console.print(f"[dim cyan]ℹ[/dim cyan] {message}")
