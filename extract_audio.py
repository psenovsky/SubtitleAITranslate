import argparse
import configparser
import os

import config_helper
from audio_extract import (
    check_ffmpeg,
    display_audio_streams,
    extract_audio,
    generate_output_path,
    get_audio_streams,
)


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    config_helper.migrate_old_config(config)
    config_helper.ensure_general_section(config)
    config_helper.ensure_active_model(config)
    description = (
        f"Version: {config['general']['version']}\n"
        "Extract audio streams from video files."
    )
    parser = argparse.ArgumentParser(
        prog="extract_audio.py",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-f", "--file", help="video file path", required=True)
    parser.add_argument("-s", "--stream", type=int, help="stream index to extract")
    parser.add_argument(
        "-a", "--all", action="store_true", help="extract all audio streams"
    )
    parser.add_argument(
        "--list", action="store_true", help="list audio streams only, do not extract"
    )
    parser.add_argument("-o", "--output-dir", help="output directory (default: same as video)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: file {args.file} does not exist.")
        exit(1)

    if not check_ffmpeg():
        exit(1)

    print("Detecting audio streams...")
    streams = get_audio_streams(args.file)

    if not streams:
        print("No audio streams found.")
        exit(1)

    display_audio_streams(streams)

    if args.list:
        exit(0)

    to_extract = []

    if args.stream is not None:
        idx = args.stream
        match = [s for s in streams if s["index"] == idx]
        if not match:
            print(f"Error: stream index {idx} not found.")
            exit(1)
        to_extract = [match[0]]
    elif args.all:
        to_extract = streams
    elif len(streams) == 1:
        to_extract = [streams[0]]
    else:
        prompt = "Which stream to extract? ("
        options = [str(i) for i in range(1, len(streams) + 1)] + ["all"]
        prompt += "/".join(options) + "): "
        choice = input(prompt).strip().lower()

        if choice == "all":
            to_extract = streams
        else:
            try:
                num = int(choice)
                if 1 <= num <= len(streams):
                    to_extract = [streams[num - 1]]
                else:
                    print(f"Error: {num} is not a valid option.")
                    exit(1)
            except ValueError:
                print(f"Error: '{choice}' is not a valid option.")
                exit(1)

    out_dir = os.path.abspath(args.output_dir) if args.output_dir else os.path.dirname(os.path.abspath(args.file))
    os.makedirs(out_dir, exist_ok=True)

    extracted = []
    for s in to_extract:
        lang = s["language"]
        out_path = generate_output_path(args.file, lang, args.output_dir)
        print(f"Extracting stream {s['index']} ({lang})...")
        if extract_audio(args.file, s["index"], out_path):
            extracted.append(out_path)
            print(f"  Saved: {out_path}")
        else:
            print(f"  Failed to extract stream {s['index']}.")

    print(f"\nDone. Extracted {len(extracted)} file(s).")


if __name__ == "__main__":
    main()
