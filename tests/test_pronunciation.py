"""Tests for pronunciation audio module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wut.audio.pronunciation import (
    AudioPlayerNotFoundError,
    PlaybackError,
    PronunciationPlayer,
    TTSError,
    _find_audio_player,
    is_audio_available,
)


def test_find_audio_player_darwin_afplay() -> None:
    """Use afplay on macOS when available."""
    with (
        patch("wut.audio.pronunciation.platform.system", return_value="Darwin"),
        patch("wut.audio.pronunciation.shutil.which") as mock_which,
    ):
        mock_which.side_effect = lambda cmd: "/usr/bin/afplay" if cmd == "afplay" else None
        player, args = _find_audio_player()

    assert player == "afplay"
    assert args == []


def test_find_audio_player_not_found() -> None:
    """Raise when no compatible player exists."""
    with (
        patch("wut.audio.pronunciation.platform.system", return_value="Linux"),
        patch("wut.audio.pronunciation.shutil.which", return_value=None),
        pytest.raises(AudioPlayerNotFoundError),
    ):
        _find_audio_player()


def test_play_success_blocking() -> None:
    """Generate and play audio, then clean up in blocking mode."""
    player = PronunciationPlayer()
    mock_tts = MagicMock()
    mock_process = MagicMock()
    mock_process.poll.return_value = None

    with (
        patch("wut.audio.pronunciation.gTTS", return_value=mock_tts) as mock_gtts,
        patch("wut.audio.pronunciation._find_audio_player", return_value=("ffplay", ["-nodisp"])),
        patch("wut.audio.pronunciation.subprocess.Popen", return_value=mock_process),
    ):
        player.play("hello", block=True)

    mock_gtts.assert_called_once_with(text="hello", lang="en", slow=False)
    mock_tts.save.assert_called_once()
    mock_process.wait.assert_called_once()
    assert player.is_playing is False


def test_play_tts_failure() -> None:
    """Wrap text-to-speech failures."""
    player = PronunciationPlayer()

    with (
        patch("wut.audio.pronunciation.gTTS", side_effect=RuntimeError("boom")),
        pytest.raises(TTSError, match="Failed to generate pronunciation"),
    ):
        player.play("hello", block=True)

    assert player._temp_file is None


def test_playback_failure_cleans_up() -> None:
    """Wrap playback errors and clean temporary state."""
    player = PronunciationPlayer()
    mock_tts = MagicMock()

    with (
        patch("wut.audio.pronunciation.gTTS", return_value=mock_tts),
        patch("wut.audio.pronunciation._find_audio_player", return_value=("ffplay", [])),
        patch("wut.audio.pronunciation.subprocess.Popen", side_effect=OSError("spawn failed")),
        pytest.raises(PlaybackError, match="Failed to play audio"),
    ):
        player.play("hello", block=True)

    assert player._temp_file is None
    assert player._process is None


def test_windows_template_player_replaces_path() -> None:
    """Replace {file} placeholder for template-style player args."""
    player = PronunciationPlayer()
    mock_tts = MagicMock()
    mock_process = MagicMock()

    with (
        patch("wut.audio.pronunciation.gTTS", return_value=mock_tts),
        patch(
            "wut.audio.pronunciation._find_audio_player",
            return_value=("powershell", ["-c", "Play '{file}'"]),
        ),
        patch("wut.audio.pronunciation.subprocess.Popen", return_value=mock_process) as mock_popen,
    ):
        player.play("hello", block=False)

    cmd = mock_popen.call_args.args[0]
    assert cmd[0] == "powershell"
    assert "{file}" not in " ".join(cmd)
    player.close()


def test_stop_uses_kill_fallback_when_terminate_fails() -> None:
    """Kill process if terminate fails."""
    player = PronunciationPlayer()
    process = MagicMock()
    process.terminate.side_effect = RuntimeError("terminate failed")
    process.wait.return_value = 0
    player._process = process
    player._temp_file = Path("/tmp/does-not-exist.mp3")

    player.stop()

    process.kill.assert_called_once()
    assert player._process is None
    assert player._temp_file is None


def test_is_audio_available() -> None:
    """Return availability status from player detection."""
    with patch("wut.audio.pronunciation._find_audio_player", return_value=("ffplay", [])):
        assert is_audio_available() is True

    with patch(
        "wut.audio.pronunciation._find_audio_player",
        side_effect=AudioPlayerNotFoundError("missing"),
    ):
        assert is_audio_available() is False
