"""Command-line interface for wut dictionary."""

import sys
from typing import NoReturn

import click
from rich.console import Console
from rich.prompt import Confirm

from wut import __version__
from wut.api.dictionary import (
    APIConnectionError,
    APITimeoutError,
    DictionaryClient,
    WordNotFoundError,
)
from wut.audio.pronunciation import PronunciationError, PronunciationPlayer
from wut.core.bookmarks import (
    BookmarkExistsError,
    BookmarkManager,
    BookmarkNotFoundError,
)
from wut.core.models import Word
from wut.display.formatter import WordFormatter

# Global instances
console = Console()
formatter = WordFormatter(console=console)


class Context:
    """CLI context object for dependency injection."""

    def __init__(self) -> None:
        self.bookmark_manager: BookmarkManager | None = None
        self.dictionary_client: DictionaryClient | None = None
        self.pronunciation_player: PronunciationPlayer | None = None
        self.interactive: bool = False

    def get_bookmark_manager(self) -> BookmarkManager:
        """Get or create bookmark manager."""
        if self.bookmark_manager is None:
            self.bookmark_manager = BookmarkManager()
        return self.bookmark_manager

    def get_dictionary_client(self) -> DictionaryClient:
        """Get or create dictionary client."""
        if self.dictionary_client is None:
            self.dictionary_client = DictionaryClient()
        return self.dictionary_client

    def get_pronunciation_player(self) -> PronunciationPlayer:
        """Get or create pronunciation player."""
        if self.pronunciation_player is None:
            self.pronunciation_player = PronunciationPlayer()
        return self.pronunciation_player

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.bookmark_manager is not None:
            self.bookmark_manager.close()
        if self.dictionary_client is not None:
            self.dictionary_client.close()
        if self.pronunciation_player is not None:
            self.pronunciation_player.close()


pass_context = click.make_pass_decorator(Context, ensure=True)


def handle_error(message: str, exit_code: int = 1) -> NoReturn:
    """Display error and exit."""
    formatter.display_error(message)
    sys.exit(exit_code)


class DefaultCommandGroup(click.Group):
    """Custom Group that treats unknown commands as words to look up.

    This allows `wut hello` to work as a word lookup while still supporting
    subcommands like `wut bookmark list` and `wut info`.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Parse args, treating unknown first arg as word to look up."""
        # If no args, let normal processing handle it (shows help)
        if not args:
            return super().parse_args(ctx=ctx, args=args)

        # Check if first arg looks like an option (starts with -)
        if args[0].startswith("-"):
            return super().parse_args(ctx=ctx, args=args)

        # Check if first arg is a known subcommand
        if args[0] in self.commands:
            return super().parse_args(ctx=ctx, args=args)

        # First arg is not a subcommand - treat as word lookup
        # Insert 'lookup' command before the word
        return super().parse_args(ctx=ctx, args=["lookup"] + args)


@click.group(
    cls=DefaultCommandGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="wut")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Wut? - A CLI dictionary with pronunciation and bookmarking.

    Look up words, hear pronunciations, and save favorites.

    \b
    Examples:
        wut hello              # Look up a word
        wut hello -p           # Look up and pronounce
        wut hello -b           # Look up and bookmark
        wut hello -i           # Interactive mode (prompts)
        wut bookmark list      # View bookmarks
    """
    ctx.ensure_object(Context)

    # Show help if no command given
    if ctx.invoked_subcommand is None:
        click.echo(message=ctx.get_help())


@main.command()
@click.argument("word")
@click.option(
    "-p",
    "--pronounce",
    is_flag=True,
    help="Play pronunciation after lookup",
)
@click.option(
    "-b",
    "--bookmark",
    "do_bookmark",
    is_flag=True,
    help="Bookmark the word after lookup",
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Enable interactive prompts",
)
@pass_context
def lookup(
    ctx: Context,
    word: str,
    pronounce: bool,
    do_bookmark: bool,
    interactive: bool,
) -> None:
    """Look up a word in the dictionary.

    \b
    Examples:
        wut hello              # Look up a word
        wut hello -p           # Look up and pronounce
        wut hello -b           # Look up and bookmark
        wut hello -i           # Interactive mode (prompts)
    """
    ctx.interactive = interactive
    _do_lookup(ctx=ctx, word=word, pronounce=pronounce, bookmark=do_bookmark)


def _do_lookup(ctx: Context, word: str, pronounce: bool, bookmark: bool) -> None:
    """Perform word lookup with optional pronunciation and bookmarking."""
    client = ctx.get_dictionary_client()

    try:
        with console.status(status=f"Looking up '{word}'..."):
            result = client.lookup(word=word)
    except WordNotFoundError:
        handle_error(message=f"Word '{word}' not found in dictionary.")
    except APITimeoutError:
        handle_error(message="Connection timed out. Please try again.")
    except APIConnectionError:
        handle_error(message="Could not connect to dictionary. Check your internet connection.")

    # Display results
    formatter.display_word(word=result)

    # Handle pronunciation
    if (
        pronounce
        or ctx.interactive
        and Confirm.ask(prompt="\n[yellow]Play pronunciation?[/yellow]", default=False)
    ):
        _play_pronunciation(ctx=ctx, word=word)

    # Handle bookmarking
    if (
        bookmark
        or ctx.interactive
        and Confirm.ask(prompt="[yellow]Bookmark this word?[/yellow]", default=False)
    ):
        _add_bookmark(ctx=ctx, word_result=result)


def _play_pronunciation(ctx: Context, word: str) -> None:
    """Play word pronunciation."""
    player = ctx.get_pronunciation_player()
    try:
        with console.status(status="Playing pronunciation..."):
            player.play(word=word, block=True)
    except PronunciationError as e:
        formatter.display_warning(message=f"Could not play pronunciation: {e}")


def _add_bookmark(ctx: Context, word_result: Word) -> None:
    """Add word to bookmarks."""
    manager = ctx.get_bookmark_manager()
    try:
        manager.add_word(word=word_result)
        formatter.display_success(message=f"Bookmarked '{word_result.word}'")
    except BookmarkExistsError:
        formatter.display_warning(message=f"'{word_result.word}' is already bookmarked.")


# Bookmark command group
@main.group()
def bookmark() -> None:
    """Manage bookmarked words.

    \b
    Commands:
        add     Add a word to bookmarks
        list    Show all bookmarks
        show    Show details of a bookmark
        delete  Remove a bookmark
        clear   Remove all bookmarks
    """
    pass


@bookmark.command("add")
@click.argument("word")
@pass_context
def bookmark_add(ctx: Context, word: str) -> None:
    """Add a word to bookmarks.

    Looks up the word and saves it to your bookmarks.
    """
    client = ctx.get_dictionary_client()
    manager = ctx.get_bookmark_manager()

    # First look up the word
    try:
        with console.status(status=f"Looking up '{word}'..."):
            result = client.lookup(word=word)
    except WordNotFoundError:
        handle_error(message=f"Word '{word}' not found in dictionary.")
    except (APITimeoutError, APIConnectionError) as e:
        handle_error(message=str(e))

    # Add to bookmarks
    try:
        manager.add_word(word=result)
        formatter.display_success(message=f"Bookmarked '{word}'")
    except BookmarkExistsError:
        formatter.display_warning(message=f"'{word}' is already bookmarked.")


@bookmark.command("list")
@click.option(
    "-l",
    "--limit",
    default=20,
    help="Maximum number of bookmarks to show",
    type=int,
)
@click.option(
    "-s",
    "--search",
    help="Filter bookmarks by prefix",
    metavar="QUERY",
)
@pass_context
def bookmark_list(ctx: Context, limit: int, search: str | None) -> None:
    """List all bookmarked words."""
    manager = ctx.get_bookmark_manager()

    bookmarks = (
        manager.search(query=search, limit=limit) if search else manager.list_all(limit=limit)
    )

    formatter.display_bookmark_list(bookmarks=bookmarks)


@bookmark.command("show")
@click.argument("word")
@pass_context
def bookmark_show(ctx: Context, word: str) -> None:
    """Show details of a bookmarked word."""
    manager = ctx.get_bookmark_manager()

    try:
        bm = manager.get(word=word)
        formatter.display_bookmark(bookmark=bm)
    except BookmarkNotFoundError:
        handle_error(message=f"'{word}' is not bookmarked.")


@bookmark.command("delete")
@click.argument("word")
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
@pass_context
def bookmark_delete(ctx: Context, word: str, force: bool) -> None:
    """Delete a bookmarked word."""
    manager = ctx.get_bookmark_manager()

    # Check if exists
    if not manager.exists(word=word):
        handle_error(message=f"'{word}' is not bookmarked.")

    # Confirm deletion
    if not force and not Confirm.ask(
        prompt=f"Delete bookmark for '[cyan]{word}[/cyan]'?", default=False
    ):
        formatter.display_info(message="Cancelled.")
        return

    manager.delete(word=word)
    formatter.display_success(message=f"Deleted bookmark for '{word}'")


@bookmark.command("clear")
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
@pass_context
def bookmark_clear(ctx: Context, force: bool) -> None:
    """Delete all bookmarks."""
    manager = ctx.get_bookmark_manager()
    count = manager.count()

    if count == 0:
        formatter.display_info(message="No bookmarks to delete.")
        return

    # Confirm deletion
    if not force and not Confirm.ask(
        prompt=f"Delete all [bold]{count}[/bold] bookmark(s)?",
        default=False,
    ):
        formatter.display_info(message="Cancelled.")
        return

    deleted = manager.clear()
    formatter.display_success(message=f"Deleted {deleted} bookmark(s)")


@main.command()
@click.argument("word")
@click.option(
    "-s",
    "--slow",
    is_flag=True,
    help="Use slow pronunciation",
)
@pass_context
def pronounce(ctx: Context, word: str, slow: bool) -> None:
    """Play pronunciation of a word.

    Uses text-to-speech to pronounce the word.
    """
    player = PronunciationPlayer(slow=slow)

    try:
        console.print(f"[dim]Playing pronunciation for '[cyan]{word}[/cyan]'...[/dim]")
        player.play(word=word, block=True)

        # Ask to repeat only in interactive mode
        if ctx.interactive:
            while Confirm.ask(prompt="Play again?", default=False):
                player.play(word=word, block=True)

    except PronunciationError as e:
        handle_error(message=f"Could not play pronunciation: {e}")
    finally:
        player.close()


@main.command()
@pass_context
def info(ctx: Context) -> None:
    """Show information about wut and database location."""
    manager = ctx.get_bookmark_manager()

    console.print(f"\n[bold cyan]Wut CLI[/bold cyan] v{__version__}")
    console.print()
    console.print(f"[bold]Database:[/bold] {manager.db_path}")
    console.print(f"[bold]Bookmarks:[/bold] {manager.count()}")
    console.print()


# Clean up on exit
@main.result_callback()
@click.pass_context
def cleanup(click_ctx: click.Context, /, _result: object, **_kwargs: object) -> None:
    """Clean up resources after command execution."""
    ctx = click_ctx.find_object(object_type=Context)
    if ctx:
        ctx.cleanup()


if __name__ == "__main__":
    main()
