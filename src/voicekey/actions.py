# src/voicekey/actions.py

import logging
import os
import sys
from typing import Dict, Optional
from unittest import runner
from voicekey.pty.runner import PtyRunner
from voicekey.parser.command_parser import CommandParser

logger = logging.getLogger(__name__)


class RunnerManager:
    """
    Manage PTY runners uniquely by script path.
    A script can only run once.
    """

    def __init__(self):
        self.runners: Dict[str, PtyRunner] = {}
        self.parser = CommandParser()

    def _normalize(self, script: str) -> str:
        return os.path.abspath(script)

    def run_script(self, script: str, args: Optional[list] = None):
        script = self._normalize(script)

        if script in self.runners:
            logger.warning("Script already running: %s", script)
            return

        args = args or []
        cmd = [sys.executable, script] + args

        runner = PtyRunner(cmd)

        def cleanup():
            logger.info("Script exited: %s", script)
            self.runners.pop(script, None)

        runner.start(on_exit=cleanup)

        self.runners[script] = runner
        logger.info("Started script: %s", script)

    def stop_script(self, script: str):
        script = self._normalize(script)

        runner = self.runners.get(script)
        if not runner:
            logger.warning("Script not running: %s", script)
            return

        runner.stop()
        self.runners.pop(script, None)
        logger.info("Stopped script: %s", script)

    def send_key(self, script: str, key: str, auto_enter: bool = False):
        script = self._normalize(script)

        runner = self.runners.get(script)
        if not runner:
            logger.warning("Script not running, cannot send key: %s", script)
            return

        # Use parser logic
        if len(key) == 1:
            data = self.parser._parse_press(key)
            if not data:
                data = key.encode()
        else:
            if key in self.parser.NAMED or key in self.parser.ARROWS:
                data = self.parser._parse_press(key)
            else:
                data = key.encode()

        if auto_enter and len(data) == 1:
            data += b"\n"

        runner.send(data)
        logger.info("Sent %r to %s", data, script)