import argparse

def build_parser():
    parser = argparse.ArgumentParser(prog="voicekey")
    parser.add_argument(
        "--model",
        default="src/voicekey/speech/models/vosk-model-small-en-us-0.15",
        help="Path to Vosk model"
    )
    parser.add_argument("--config", default="examples/config.yaml", help="Path to YAML config with commands")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    return parser