"""
TalentGraph AI — File Utilities

Provides safe file I/O helpers for pickle serialisation,
JSON persistence, and directory management used across the pipeline.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

from shared.logging_setup import get_logger

logger = get_logger(__name__)


def ensure_dir(path: str | Path) -> Path:
    """
    Ensure a directory exists, creating it (and parents) if necessary.

    Args:
        path: Directory path as string or Path object.

    Returns:
        Resolved Path object for the directory.

    Raises:
        OSError: If directory cannot be created due to permissions.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_pickle(obj: Any, path: str | Path) -> None:
    """
    Serialise any Python object to disk using pickle.

    Creates parent directories automatically.

    Args:
        obj: Python object to serialise (e.g., FAISS index metadata, BM25 index).
        path: Destination file path.

    Raises:
        IOError: If the file cannot be written.
    """
    p = Path(path)
    ensure_dir(p.parent)
    try:
        with open(p, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug("Saved pickle: %s", p)
    except Exception as exc:
        logger.error("Failed to save pickle to %s: %s", p, exc)
        raise


def load_pickle(path: str | Path) -> Any:
    """
    Deserialise a pickle file from disk.

    Args:
        path: Source file path.

    Returns:
        Deserialised Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read or is corrupted.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Pickle file not found: {p}")
    try:
        with open(p, "rb") as f:
            obj = pickle.load(f)
        logger.debug("Loaded pickle: %s", p)
        return obj
    except Exception as exc:
        logger.error("Failed to load pickle from %s: %s", p, exc)
        raise


def save_json(obj: dict, path: str | Path) -> None:
    """
    Serialise a dictionary to a JSON file with pretty formatting.

    Creates parent directories automatically.

    Args:
        obj: Dictionary to serialise.
        path: Destination file path.

    Raises:
        TypeError: If obj contains non-serialisable values.
        IOError: If the file cannot be written.
    """
    p = Path(path)
    ensure_dir(p.parent)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False, default=str)
        logger.debug("Saved JSON: %s", p)
    except Exception as exc:
        logger.error("Failed to save JSON to %s: %s", p, exc)
        raise


def load_json(path: str | Path) -> dict:
    """
    Load and parse a JSON file from disk.

    Args:
        path: Source file path.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON file not found: {p}")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("Loaded JSON: %s", p)
        return data
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", p, exc)
        raise
    except Exception as exc:
        logger.error("Failed to load JSON from %s: %s", p, exc)
        raise
