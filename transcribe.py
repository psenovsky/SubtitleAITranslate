import argparse
import configparser
import os

import lib.config_helper as config_helper
from lib.whisper_transcribe import (
    load_iso639_data,
    load_whisper_support,
    validate_audio_filename,
    transcribe_audio,
    segments_to_srt,
    save_srt,
)


def main():
    """CLI entry point for transcribing audio files to SRT subtitles using Whisper."""
    config = configparser.ConfigParser()
    config.read("config.ini")
    config_helper.migrate_old_config(config)
    config_helper.ensure_general_section(config)
    config_helper.ensure_active_model(config)
    description = (
        f"Version: {config['general']['version']}\n"
        "Transcribe audio files using Whisper."
    )
    parser = argparse.ArgumentParser(
        prog="transcribe.py",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-f", "--file", help="audio file path (format: video.name.lang.wav)", required=True
    )
    parser.add_argument(
        "-d", "--data-dir", help="directory with language data files (default: data/)", default="data/"
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: file {args.file} does not exist.")
        exit(1)

    print("Loading language data...")
    iso639_data = load_iso639_data(args.data_dir)
    whisper_supported = load_whisper_support(args.data_dir)

    print("Validating audio filename...")
    try:
        video_name, lang_code_639_2, lang_code_639_1, language_name = validate_audio_filename(
            os.path.basename(args.file), iso639_data
        )
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)

    print(f"  Video name: {video_name}")
    print(f"  Language: {language_name} ({lang_code_639_2}/{lang_code_639_1})")

    if lang_code_639_1 not in whisper_supported:
        print(f"Error: language '{language_name}' is not supported by Whisper.")
        print("Supported languages:", ", ".join(sorted(whisper_supported)))
        exit(1)

    print(f"\nTranscribing with Whisper (large model)...")
    print(f"  Language: {language_name}")

    try:
        segments = transcribe_audio(args.file, language_name)
    except Exception as e:
        print(f"Error during transcription: {e}")
        exit(1)

    print(f"  Generated {len(segments)} subtitle segments")

    srt_content = segments_to_srt(segments)
    output_path = os.path.splitext(args.file)[0] + ".srt"
    print(f"\nSaving SRT file to: {output_path}")

    if save_srt(srt_content, output_path):
        print("Done.")
    else:
        print("Failed to save SRT file.")
        exit(1)


if __name__ == "__main__":
    main()
