import argparse  # parses command line arguments
import configparser  # reads configuration files
import os  # file system operations

import config_helper
from subtitle_trans import translate_subtitles


def main():
    """CLI entry point for translating subtitle files using a local LLM."""
    config = configparser.ConfigParser()
    config.read("config.ini")
    config_helper.migrate_old_config(config)
    config_helper.ensure_general_section(config)
    config_helper.ensure_active_model(config)
    description = (
        f"Version: {config['general']['version']}\nTranslate subtitles using local AI."
    )
    parser = argparse.ArgumentParser(
        prog="translate.py",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-f", "--subFile", help="SRT with subtitles")
    parser.add_argument("-t", "--subTarget", help="target language", default="czech")
    parser.add_argument("-s", "--subSource", help="source language", default="english")
    parser.add_argument(
        "-o", "--outputFile", help="output file name", default="translated.srt"
    )
    parser.add_argument(
        "-m", "--model", help="AI model name to use (default: active model)", default=None
    )
    args = parser.parse_args()
    sub = None
    if not os.path.exists(args.subFile):
        print(f"❌ subtitel file {args.subFile} does not exist.")
        exit()
    else:
        f = open(args.subFile, "r")
        sub = f.read()
        f.close()

    # Call the translation function with parsed arguments
    x = translate_subtitles(
        subtitles=sub,
        language_from=args.subSource,
        language_to=args.subTarget,
        config=config,
        model_name=args.model,
    )

    # Write the translated subtitles to a file
    with open(args.outputFile, "w") as f:
        f.write(x)

    print(f"\n\n✅ Translated subtitles saved to {args.outputFile}")


if __name__ == "__main__":
    main()
