"""
TalentGraph AI — Preprocessing Pipeline Checkpoints

Provides utility to save and load pipeline state for crash recovery
and resuming long-running operations.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """
    Manages loading, saving, and checking status of pipeline checkpoints.
    """

    def __init__(self, checkpoint_dir: str = settings.preprocessing_checkpoint_path) -> None:
        """Initialize checkpoint directory."""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"CheckpointManager initialised at {self.checkpoint_dir}")

    def save(self, name: str, state: dict[str, Any]) -> None:
        """
        Save the current state to a checkpoint file.

        Args:
            name: Checkpoint identifier name.
            state: Dictionary containing state info to serialize.
        """
        checkpoint_file = self.checkpoint_dir / f"{name}.ckpt.json"
        state["updated_at"] = datetime.now().isoformat()
        try:
            with checkpoint_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            logger.info(f"Checkpoint '{name}' saved successfully")
        except Exception as e:
            logger.error(f"Failed to save checkpoint '{name}': {e}")

    def load(self, name: str) -> dict[str, Any] | None:
        """
        Load state from a checkpoint file.

        Args:
            name: Checkpoint identifier name.

        Returns:
            The loaded state dictionary, or None if not found or failed.
        """
        checkpoint_file = self.checkpoint_dir / f"{name}.ckpt.json"
        if not checkpoint_file.exists():
            logger.debug(f"No checkpoint file found at {checkpoint_file}")
            return None

        try:
            with checkpoint_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
            logger.info(f"Checkpoint '{name}' loaded successfully")
            return state
        except Exception as e:
            logger.error(f"Failed to load checkpoint '{name}': {e}")
            return None

    def clear(self, name: str) -> None:
        """Delete a checkpoint file if it exists."""
        checkpoint_file = self.checkpoint_dir / f"{name}.ckpt.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"Checkpoint '{name}' cleared")

    def clear_all(self) -> None:
        """Delete all checkpoint files in the directory."""
        for file in self.checkpoint_dir.glob("*.ckpt.json"):
            file.unlink()
        logger.info("All checkpoints cleared")

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """
        Retrieve completion status and details for all pipeline stages.

        Returns:
            A dictionary mapping stage name to status details.
        """
        stages = ["loading", "cleaning", "parsing", "features", "indexing"]
        status = {}
        for stage in stages:
            state = self.load(stage)
            if state:
                status[stage] = {
                    "complete": state.get("complete", False),
                    "processed_count": state.get("processed_count", 0),
                    "updated_at": state.get("updated_at", "Unknown"),
                }
            else:
                status[stage] = {
                    "complete": False,
                    "processed_count": 0,
                    "updated_at": "Never",
                }
        return status
