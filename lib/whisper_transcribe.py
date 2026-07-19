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


def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _get_device():
    """Detect the best available device for Whisper inference."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def transcribe_audio(audio_path, language_name, model_size="turbo"):
    """Transcribe audio file using Whisper model.

    Args:
        audio_path: Path to the WAV audio file
        language_name: Language name (e.g., 'English') for Whisper
        model_size: Whisper model size ('small', 'medium', 'turbo', 'large')

    Returns:
        List of segments, each with 'start', 'end', 'text' keys
    """
    import whisper

    device = _get_device()
    print(f"Whisper using device: {device}, model: {model_size}")

    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_path, language=language_name)

    return result["segments"]


def segments_to_srt(segments):
    """Convert Whisper segments to SRT format string.

    Args:
        segments: List of dicts with 'start', 'end', 'text' keys

    Returns:
        SRT formatted string
    """
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def save_srt(srt_content, output_path):
    """Save SRT content to file.

    Args:
        srt_content: SRT formatted string
        output_path: Path to output .srt file

    Returns:
        True on success, False on failure
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        return True
    except Exception as e:
        print(f"Error saving SRT file: {e}")
        return False
