import threading
import time
import logging
from sshkeyboard import listen_keyboard, stop_listening

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state flags (same idea as your original program)
START = False
STOP = False
RECORD_TOGGLE = False


def on_press(key):
    """
    This function is called automatically whenever a key is pressed.
    """
    global START, STOP, RECORD_TOGGLE

    if key == 'r':
        START = True
        logger.info("Pressed [r] → START = True")

    elif key == 's' and START:
        RECORD_TOGGLE = not RECORD_TOGGLE
        logger.info(f"Pressed [s] → RECORD_TOGGLE = {RECORD_TOGGLE}")

    elif key == 'q':
        STOP = True
        logger.info("Pressed [q] → STOP = True (Exiting)")

    else:
        logger.info(f"Pressed [{key}] → No action assigned")


if __name__ == "__main__":

    logger.info("🟢 Press [r] to set START = True")
    logger.info("🟡 Press [s] to toggle RECORD_TOGGLE (only if started)")
    logger.info("🔴 Press [q] to quit")

    # Start keyboard listener in separate thread (same pattern as your program)
    keyboard_thread = threading.Thread(
        target=listen_keyboard,
        kwargs={
            "on_press": on_press,
            "until": None,
            "sequential": False,
        },
        daemon=True,
    )

    keyboard_thread.start()

    # Main loop (does nothing except wait for STOP)
    while not STOP:
        time.sleep(0.1)

    # Clean shutdown
    stop_listening()
    keyboard_thread.join()

    logger.info("✅ Program exited cleanly.")