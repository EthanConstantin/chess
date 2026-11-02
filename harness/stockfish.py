"""Download and locate the pinned Stockfish build used as the Elo reference.

The version is pinned on purpose: Elo is only comparable across engine versions if the
reference opponents never change. Bumping STOCKFISH_TAG means re-running every version.
"""

import platform
import shutil
import stat
import tarfile
import urllib.request
import zipfile
from pathlib import Path

STOCKFISH_TAG = "sf_19"
ROOT = Path(__file__).resolve().parent.parent
INSTALL_DIR = ROOT / "tools" / "stockfish"


def _asset_name() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "x86-64"
    if system == "Windows":
        return f"stockfish-windows-{arch}-universal.zip"
    if system == "Darwin":
        return "stockfish-macos-universal.tar.gz"
    if system == "Linux":
        return f"stockfish-linux-{arch}-universal.tar.gz"
    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def find_stockfish() -> Path | None:
    """Return the installed Stockfish executable, or None if it is not installed."""
    if not INSTALL_DIR.exists():
        return None
    for path in sorted(INSTALL_DIR.rglob("stockfish*")):
        if path.is_file() and path.suffix in ("", ".exe") and "." not in path.stem.replace("-", ""):
            return path
    return None


def install_stockfish(force: bool = False) -> Path:
    """Download the pinned Stockfish release into tools/stockfish (gitignored)."""
    existing = find_stockfish()
    if existing and not force:
        return existing

    asset = _asset_name()
    url = f"https://github.com/official-stockfish/Stockfish/releases/download/{STOCKFISH_TAG}/{asset}"
    if INSTALL_DIR.exists():
        shutil.rmtree(INSTALL_DIR)
    INSTALL_DIR.mkdir(parents=True)
    archive = INSTALL_DIR / asset

    print(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, archive)

    if asset.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(INSTALL_DIR)
    else:
        with tarfile.open(archive) as tf:
            tf.extractall(INSTALL_DIR, filter="data")
    archive.unlink()

    exe = find_stockfish()
    if exe is None:
        raise RuntimeError(f"Stockfish executable not found after extracting {asset}")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    print(f"Installed Stockfish {STOCKFISH_TAG} at {exe}")
    return exe
