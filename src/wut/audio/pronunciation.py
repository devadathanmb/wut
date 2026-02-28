"""Audio pronunciation using gTTS and system audio players."""

import contextlib
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from gtts import gTTS  # type: ignore[import-untyped]


class PronunciationError(Exception):
    """Base exception for pronunciation errors."""


class TTSError(PronunciationError):
    """Error during text-to-speech generation."""


class PlaybackError(PronunciationError):
    """Error during audio playback."""


class AudioPlayerNotFoundError(PronunciationError):
    """No suitable audio player found on system."""


def _find_audio_player() -> tuple[str, list[str]]:
    """Find an available audio player on the system.

    Returns:
        Tuple of (player_path, extra_args).

    Raises:
        AudioPlayerNotFoundError: If no player is found.
    """
    system = platform.system()

    # Platform-specific players
    if system == "Darwin" and shutil.which("afplay"):  # macOS
        return "afplay", []

    if system == "Windows" and shutil.which("powershell"):
        # Use PowerShell to play audio on Windows
        return "powershell", [
            "-c",
            "(New-Object Media.SoundPlayer '{file}').PlaySync()",
        ]

    # Cross-platform players
    if shutil.which("ffplay"):
        return "ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]

    if shutil.which("mpv"):
        return "mpv", ["--no-video", "--really-quiet"]

    if shutil.which("paplay"):  # PulseAudio (Linux)
        return "paplay", []

    if shutil.which("aplay"):  # ALSA (Linux)
        # Note: aplay only works with WAV, would need conversion
        pass

    raise AudioPlayerNotFoundError(
        "No audio player found. Install ffplay, mpv, or another audio player."
    )


class PronunciationPlayer:
    """Player for word pronunciations using gTTS and system audio players."""

    def __init__(self, *, lang: str = "en", slow: bool = False) -> None:
        """Initialize pronunciation player.

        Args:
            lang: Language code for TTS (default: English).
            slow: Whether to use slow pronunciation.
        """
        self._lang = lang
        self._slow = slow
        self._temp_file: Path | None = None
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def play(self, word: str, *, block: bool = True) -> None:
        """Play pronunciation of a word.

        Args:
            word: Word to pronounce.
            block: Whether to block until playback completes.

        Raises:
            TTSError: If TTS generation fails.
            PlaybackError: If audio playback fails.
            AudioPlayerNotFoundError: If no audio player is available.
        """
        self._cleanup()

        # Generate TTS audio
        try:
            tts = gTTS(text=word, lang=self._lang, slow=self._slow)
            fd, temp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            self._temp_file = Path(temp_path)
            tts.save(str(self._temp_file))
        except Exception as e:
            self._cleanup()
            raise TTSError(f"Failed to generate pronunciation: {e}") from e

        # Find and use audio player
        try:
            player, args = _find_audio_player()
        except AudioPlayerNotFoundError:
            self._cleanup()
            raise

        # Build command
        try:
            if "{file}" in str(args):
                # Special handling for PowerShell-style commands
                cmd = [player] + [arg.replace("{file}", str(self._temp_file)) for arg in args]
            else:
                cmd = [player, *args, str(self._temp_file)]

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if block:
                self._wait_for_playback()
        except Exception as e:
            self._cleanup()
            raise PlaybackError(f"Failed to play audio: {e}") from e

    def _wait_for_playback(self) -> None:
        """Wait for current playback to complete."""
        if self._process is not None:
            self._process.wait()
            self._process = None
        self._cleanup()

    def stop(self) -> None:
        """Stop current playback."""
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except Exception:
                with contextlib.suppress(Exception):
                    self._process.kill()
            finally:
                self._process = None
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up temporary audio file."""
        if self._temp_file is not None:
            try:
                self._temp_file.unlink(missing_ok=True)
            except Exception:
                pass
            finally:
                self._temp_file = None

    def close(self) -> None:
        """Close player and release resources."""
        self.stop()

    def __enter__(self) -> "PronunciationPlayer":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        self.close()


# Convenience function for one-off pronunciation
def pronounce_word(word: str, *, lang: str = "en", slow: bool = False) -> None:
    """Play pronunciation of a word.

    Args:
        word: Word to pronounce.
        lang: Language code.
        slow: Whether to use slow pronunciation.
    """
    with PronunciationPlayer(lang=lang, slow=slow) as player:
        player.play(word=word, block=True)


def is_audio_available() -> bool:
    """Check if audio playback is available on this system.

    Returns:
        True if an audio player is available.
    """
    try:
        _find_audio_player()
        return True
    except AudioPlayerNotFoundError:
        return False
