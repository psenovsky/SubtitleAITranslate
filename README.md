# SubtitleAITranslate

## About

Simple command line utility (and GUI) for quick and dirty automatic translation of subtitles using local AI such as OpenAI GPT-OSS using Ollama or LM-Studio.

Please note that the AI is supposed to run locally, which means that the app does not implement any kind of authentication or authorization. In other words, use with caution.

## Configuration

The app is configured using a simple ini file. The file is located in the same folder as the executable. The file name is `config.ini`. The default configuration is as follows:

```
[AI]
host = 127.0.0.1
port = 1234
model = deepreinforce-ai/Orinth-1.0-9b
max_tokens = 200000
min_batch_size = 3
max_batch_size = 30

[general]
version = 0.0.2
```

The configuration directives are:

- `host` — address of the AI server (expected to run locally)
- `port` — port of the AI server
- `model` — the LLM model name to use for translation
- `max_tokens` — maximum number of tokens in the AI response
- `min_batch_size` — minimum number of subtitles in a batch; if a batch is smaller, it is merged with the previous one
- `max_batch_size` — maximum number of subtitles per batch sent to the AI server in one request
- `version` — informational, version of the app used in the CLI help output

Alternatively you can use the GUI to configure the app.

Be aware that `max_tokens` depends on the model you are using and may need to be adjusted. Some models are more talkative than others and use more tokens to perform the translation. You may also need to adjust the batch size parameters (`min_batch_size` and `max_batch_size`) depending on the model used and available resources.

## Usage

### Command line

```
usage: translate.py [-h] [-f PATH] [-t TARGET_LANGUAGE] [-s SOURCE_LANGUAGE] [-o OUTPUT_FILE]

optional arguments:
  -h, --help                show this help message and exit
  -f, --subFile PATH        path to subtitle file in SRT format
  -t, --subTarget TARGET_LANGUAGE, target language of the subtitle file (default czech)
  -s, --subSource SOURCE_LANGUAGE, source language of the subtitle file (default english)
  -o, --outFile PATH        path to output file in SRT format (default translated.srt)
```

#### Example

```
uv run translate.py -f subtitles.srt -t czech -s english -o output.srt
```

### GUI

A graphical interface is also available. Launch it with:

```
uv run python run_gui.py
```

The GUI provides a form where you can:

- Browse and select the source subtitle file (`.srt`)
- Browse and select the target file path
- Set source and target languages (prefilled with English and Czech)
- Click **GO** to start the translation

The translation runs in the background so the window stays responsive. A status message at the bottom indicates progress and completion.

## Audio Extraction

Extracts audio streams from video files. Requires `ffmpeg` and `ffprobe` to be installed and available on PATH.

### Usage

```
usage: extract_audio.py [-h] -f FILE [-s STREAM] [-a] [--list] [-o OUTPUT_DIR]

options:
  -h, --help            show this help message and exit
  -f, --file FILE       video file path
  -s, --stream STREAM   stream index to extract
  -a, --all             extract all audio streams
  --list                list audio streams only, do not extract
  -o, --output-dir      output directory (default: same as video)
```

### Examples

List audio streams in a video file:

```
uv run extract_audio.py -f video.mkv --list
```

Extract audio (auto-selects if only one stream):

```
uv run extract_audio.py -f video.mkv
```

Extract a specific stream by index:

```
uv run extract_audio.py -f video.mkv -s 1
```

Extract all audio streams:

```
uv run extract_audio.py -f video.mkv -a
```

### Output

Extracted audio is saved as WAV files (PCM 16-bit, 16kHz, mono) in the same directory as the input video by default. The output filename follows the pattern `<original_name>.<language_code>.wav`, for example:

```
video.mkv  -->  video.eng.wav
```

These settings are optimized for use with Whisper-based speech recognition to be implemented at later time.
