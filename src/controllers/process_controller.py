"""
Process Controller - Coordinates between UI and ProcessManager/ProcessExecutor

Responsabilidades:
- Coordinar entre UI y managers
- Validar datos antes de guardar
- Manejar eventos de UI
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.process import Process
from core.process_manager import ProcessManager
from core.process_executor import ProcessExecutor
from database.db_manager import DBManager

logger = logging.getLogger(__name__)


class ProcessController(QObject):
    """Controller for process operations"""

    # Signal emitted when a process is activated/deactivated
    process_state_changed = pyqtSignal(int, bool)  # process_id, is_active

    def __init__(self, db_manager: DBManager, config_manager=None, clipboard_manager=None, list_controller=None):
        """
        Initialize ProcessController

        Args:
            db_manager: Database manager instance
            config_manager: Config manager instance
            clipboard_manager: Clipboard manager instance
            list_controller: List controller instance (for accessing lists)
        """
        super().__init__()

        self.db_manager = db_manager
        self.config_manager = config_manager
        self.clipboard_manager = clipboard_manager
        self.list_controller = list_controller

        # Initialize managers
        self.process_manager = ProcessManager(db_manager)
        self.process_executor = ProcessExecutor(db_manager, clipboard_manager)

        logger.info("ProcessController initialized")

    # ==================== PROCESS CRUD ====================

    def create_process(self, process: Process) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new process

        Args:
            process: Process object to create

        Returns:
            Tuple of (success, message, process_id)
        """
        return self.process_manager.create_process(process)

    def save_process(self, process: Process) -> Tuple[bool, str]:
        """
        Save (update) an existing process

        Args:
            process: Process object with updated data

        Returns:
            Tuple of (success, message)
        """
        return self.process_manager.update_process(process)

    def get_process(self, process_id: int) -> Optional[Process]:
        """Get process by ID"""
        return self.process_manager.get_process(process_id)

    def get_process_steps(self, process_id: int) -> List:
        """Get all steps for a process"""
        process = self.process_manager.get_process(process_id)
        if process:
            return process.steps
        return []

    def get_all_processes(self, include_archived: bool = False, include_inactive: bool = False):
        """Get all processes"""
        return self.process_manager.get_all_processes(
            include_archived=include_archived,
            include_inactive=include_inactive
        )

    def delete_process(self, process_id: int) -> Tuple[bool, str]:
        """Delete a process"""
        return self.process_manager.delete_process(process_id)

    # ==================== EXECUTION ====================

    def execute_process(self, process_id: int) -> bool:
        """
        Execute a process

        Args:
            process_id: Process ID

        Returns:
            Success status
        """
        # Get process
        process = self.process_manager.get_process(process_id)
        if not process:
            logger.error(f"Process {process_id} not found")
            return False

        # Execute
        return self.process_executor.execute_process(process)

    def get_executor(self) -> ProcessExecutor:
        """Get process executor instance"""
        return self.process_executor

    def update_process_pin(self, process_id: int, is_pinned: bool) -> bool:
        """
        Update process pin state

        Args:
            process_id: Process ID
            is_pinned: New pin state

        Returns:
            Success status
        """
        try:
            # Get process
            process = self.process_manager.get_process(process_id)
            if not process:
                logger.error(f"Process {process_id} not found")
                return False

            # Update pin state
            process.is_pinned = is_pinned

            # Save to database
            success, msg = self.process_manager.update_process(process)

            if success:
                logger.info(f"Process {process_id} pin state updated to {is_pinned}")
            else:
                logger.error(f"Failed to update pin state: {msg}")

            return success
        except Exception as e:
            logger.error(f"Exception updating pin state: {e}")
            return False

    def toggle_process_active(self, process_id: int) -> bool:
        """
        Toggle active state of a process

        Args:
            process_id: Process ID

        Returns:
            Success status
        """
        try:
            # Get process
            process = self.process_manager.get_process(process_id)
            if not process:
                logger.error(f"Process {process_id} not found")
                return False

            # Toggle is_active
            process.is_active = not process.is_active

            # Save to database
            success, msg = self.process_manager.update_process(process)

            if success:
                logger.info(f"Process {process_id} active state updated to {process.is_active}")
                # Emit signal for UI refresh
                self.process_state_changed.emit(process_id, process.is_active)
            else:
                logger.error(f"Failed to update active state: {msg}")

            return success
        except Exception as e:
            logger.error(f"Exception toggling active state: {e}")
            return False

    def set_process_active(self, process_id: int, is_active: bool) -> bool:
        """
        Set active state of a process

        Args:
            process_id: Process ID
            is_active: New active state

        Returns:
            Success status
        """
        try:
            # Get process
            process = self.process_manager.get_process(process_id)
            if not process:
                logger.error(f"Process {process_id} not found")
                return False

            # Check if state is already set
            if process.is_active == is_active:
                logger.info(f"Process {process_id} already has is_active={is_active}")
                return True

            # Update is_active
            process.is_active = is_active

            # Save to database
            success, msg = self.process_manager.update_process(process)

            if success:
                logger.info(f"Process {process_id} active state updated to {is_active}")
                # Emit signal for UI refresh
                self.process_state_changed.emit(process_id, is_active)
            else:
                logger.error(f"Failed to update active state: {msg}")

            return success
        except Exception as e:
            logger.error(f"Exception setting active state: {e}")
            return False
