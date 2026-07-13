import json
import os
import shutil
import subprocess


def check_ffmpeg():
    """Check if ffmpeg and ffprobe are available on PATH."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg:
        print("Error: ffmpeg not found on PATH.")
        return False
    if not ffprobe:
        print("Error: ffprobe not found on PATH.")
        return False
    return True


def get_audio_streams(video_path):
    """Detect all audio streams in the given video file using ffprobe.

    Returns a list of dicts, each containing:
      - index: stream index in the file
      - codec_name: codec identifier (e.g. 'eac3', 'aac')
      - channels: number of audio channels
      - channel_layout: e.g. '5.1(side)', 'stereo'
      - language: ISO 639-2 language code from tags, or 'und' if missing
      - duration: duration string from tags, or 'N/A'
      - bit_rate: bit rate string, or 'N/A'
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "a",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running ffprobe: {result.stderr.strip()}")
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Error: could not parse ffprobe output.")
        return []

    streams = []
    for s in data.get("streams", []):
        tags = s.get("tags", {})
        bit_rate = s.get("bit_rate", "N/A")
        if bit_rate != "N/A":
            try:
                bit_rate = f"{int(bit_rate) // 1000} kbps"
            except (ValueError, TypeError):
                bit_rate = str(bit_rate)

        streams.append({
            "index": s.get("index", 0),
            "codec_name": s.get("codec_name", "unknown"),
            "channels": s.get("channels", 0),
            "channel_layout": s.get("channel_layout", "N/A"),
            "language": tags.get("language", "und"),
            "duration": tags.get("DURATION", "N/A"),
            "bit_rate": bit_rate,
        })

    return streams


def display_audio_streams(streams):
    """Pretty-print a numbered table of detected audio streams."""
    print(f"\nFound {len(streams)} audio stream(s):\n")
    print(f"  {'#':<4} {'Language':<10} {'Codec':<8} {'Channels':<10} {'Duration':<14} {'Bitrate':<12}")
    print(f"  {'-'*4} {'-'*10} {'-'*8} {'-'*10} {'-'*14} {'-'*12}")
    for i, s in enumerate(streams, 1):
        duration = s["duration"]
        if duration != "N/A" and "." in duration:
            duration = duration.split(".")[0]
        print(f"  {i:<4} {s['language']:<10} {s['codec_name']:<8} {s['channels']:<10} {duration:<14} {s['bit_rate']:<12}")
    print()


def generate_output_path(video_path, language, output_dir=None):
    """Build output WAV path: <dir>/<stem>.<language>.wav

    If output_dir is None, uses the same directory as the video file.
    """
    video_path = os.path.abspath(video_path)
    if output_dir is None:
        output_dir = os.path.dirname(video_path)
    else:
        output_dir = os.path.abspath(output_dir)

    stem = os.path.splitext(os.path.basename(video_path))[0]
    filename = f"{stem}.{language}.wav"
    return os.path.join(output_dir, filename)


def extract_audio(video_path, stream_index, output_path):
    """Extract a single audio stream from a video file to WAV.

    Uses 16kHz mono PCM 16-bit (Whisper-optimized settings).

    Returns True on success, False on failure.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-map", f"0:{stream_index}",
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error extracting stream {stream_index}: {result.stderr.strip()}")
        return False
    return True
