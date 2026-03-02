from voicekey.cli import build_parser
from voicekey.app import VoiceKeyApp

def main():
    parser = build_parser()
    args = parser.parse_args()
    app = VoiceKeyApp(model_path=args.model, config_path=args.config, verbose=args.verbose)
    app.start()

if __name__ == "__main__":
    main()