# src/voicekey/app.py
import logging
import sys
from voicekey.speech.vosk_engine import VoskEngine
from voicekey.config import load_config
from voicekey.actions import RunnerManager
import argparse
from voicekey.utils.logging import configure_logging

logger = logging.getLogger(__name__)


class VoiceKeyApp:
    def __init__(self, model_path: str, config_path: str, verbose: bool = False):
        if verbose:
            configure_logging(level="DEBUG")
        else:
            configure_logging()

        cfg = load_config(config_path)
        self.commands = {entry["phrase"]: entry["action"] for entry in cfg["commands"]}
        self.grammar = list(self.commands.keys())  # phrases used by Vosk grammar
        logger.debug("Grammar for Vosk: %s", self.grammar)
        self.runner_mgr = RunnerManager()

        self.speech = VoskEngine(model_path, grammar=self.grammar)

    def start(self):
        logger.info("Starting voicekey; available commands: %s", ", ".join(self.grammar))

        # callback when Vosk recognizes final text
        def on_text(text):
            text = text.strip().lower()
            logger.info("[voice] %s", text)
            action = self.commands.get(text)
            if not action:
                logger.warning("No action mapped for phrase '%s'", text)
                return

            self._execute_action(action)

        self.speech.start(on_text)
        try:
            # speech engine runs in background threads; main thread stays alive
            while True:
                # keep main thread alive, actions run in background (runners create threads)
                # simple sleep; you may want to add proper signal handling here
                import time
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Interrupted by user, shutting down")
        finally:
            self.shutdown()

    def _execute_action(self, action: dict):
        typ = action.get("type")

        if typ == "run":
            script = action.get("script")
            args = action.get("args", [])
            if not script:
                logger.error("Invalid run action: %s", action)
                return
            self.runner_mgr.run_script(script, args)

        elif typ == "stop":
            script = action.get("script")
            if not script:
                logger.error("Invalid stop action: %s", action)
                return
            self.runner_mgr.stop_script(script)

        elif typ == "keypress":
            script = action.get("script")
            key = action.get("key")
            auto_enter = bool(action.get("auto_enter", False))
            if not script or not key:
                logger.error("Invalid keypress action: %s", action)
                return
            self.runner_mgr.send_key(script, key, auto_enter)

        else:
            logger.error("Unknown action type: %s", typ)

    def shutdown(self):
        logger.info("Shutting down: stopping speech and all runners")
        self.speech.stop()
        # stop all runners
        for id_ in list(self.runner_mgr.runners.keys()):
            self.runner_mgr.stop_script(id_)