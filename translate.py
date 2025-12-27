import argparse  # parses command line arguments
import configparser  # reads configuration files
import os  # file system operations

from subtitle_trans import translate_subtitles


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
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
    )

    # Write the translated subtitles to a file
    with open(args.outputFile, "w") as f:
        f.write(x)

    print(f"\n\n✅ Translated subtitles saved to {args.outputFile}")


if __name__ == "__main__":
    main()
