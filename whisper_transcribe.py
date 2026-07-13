import csv
import os


def load_iso639_data(data_dir):
    """Load ISO 639-2 language codes from CSV file.

    Returns a dict mapping ISO 639-2 code to (639-1 code, language name).
    Only includes entries with valid 639-2 codes.
    """
    iso_path = os.path.join(data_dir, "iso639.csv")
    languages = {}

    with open(iso_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        header = next(reader)

        for row in reader:
            if len(row) < 5:
                continue

            code_639_2 = row[0].strip().lower()
            code_639_1 = row[3].strip().lower()
            name = row[4].strip()

            if not code_639_2 or not code_639_1 or not name:
                continue

            if " / " in code_639_2:
                code_639_2 = code_639_2.split(" / ")[0].strip()

            if len(code_639_2) == 3 and len(code_639_1) == 2:
                languages[code_639_2] = (code_639_1, name)

    return languages


def load_whisper_support(data_dir):
    """Load Whisper supported languages from CSV file.

    Returns a set of ISO 639-1 codes that Whisper supports.
    """
    whisper_path = os.path.join(data_dir, "whisper_support.csv")
    supported = set()

    with open(whisper_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        next(reader)

        for row in reader:
            if len(row) < 2:
                continue

            code_639_1 = row[0].strip().lower()
            if code_639_1:
                supported.add(code_639_1)

    return supported


def validate_audio_filename(filename, iso639_data):
    """Extract and validate language code from audio filename.

    Expected format: video.name.lang.wav where lang is ISO 639-2 code.
    Returns (video_name, lang_code_639_2, lang_code_639_1, language_name) or raises ValueError.
    """
    if not filename.endswith(".wav"):
        raise ValueError(f"File must be a .wav file: {filename}")

    base = os.path.splitext(filename)[0]

    if "." not in base:
        raise ValueError(
            f"Filename must have format 'video.name.lang.wav', got: {filename}"
        )

    video_name, lang_code = base.rsplit(".", 1)
    lang_code = lang_code.lower()

    if lang_code not in iso639_data:
        raise ValueError(
            f"Language code '{lang_code}' not found in ISO 639-2 data"
        )

    code_639_1, language_name = iso639_data[lang_code]
    return video_name, lang_code, code_639_1, language_name


def transcribe_audio(audio_path, language_name):
    """Transcribe audio file using Whisper large model.

    Args:
        audio_path: Path to the WAV audio file
        language_name: Language name (e.g., 'English') for Whisper

    Returns:
        Transcribed text
    """
    import whisper

    model = whisper.load_model("large")
    result = model.transcribe(audio_path, language=language_name)

    return result["text"]


def save_transcription(text, output_path):
    """Save transcription text to file.

    Args:
        text: Transcribed text
        output_path: Path to output .txt file

    Returns:
        True on success, False on failure
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error saving transcription: {e}")
        return False
