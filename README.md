# SubtitleAITranslate

## About

Simple command line utility (and GUI) for quick and dirty automatic translation of subtitles using local AI such as OpenAI GPT-OSS using Ollama or LM-Studio.

Please note that the AI is supposed to run locally, which means that the app does not implement any kind of authentication or authorization. In other words, use with caution.

## Configuration

The app is configured using a simple ini file. The file is located in the same folder as the executable. The file name is `config.ini`. The default configuration is as follows:

```
[general]
version = 0.0.2
active_model = default

[model.default]
host = 127.0.0.1
port = 1234
model = deepreinforce-ai/Orinth-1.0-9b
max_tokens = 200000
min_batch_size = 3
max_batch_size = 30
```

Each AI model is defined in its own section named `[model.<name>]`. The `[general]` section holds app-wide settings:

- `version` — informational, version of the app used in the CLI help output
- `active_model` — name of the model to use by default

The configuration directives for each model section are:

- `host` — address of the AI server (expected to run locally)
- `port` — port of the AI server
- `model` — the LLM model name to use for translation
- `max_tokens` — maximum number of tokens in the AI response
- `min_batch_size` — minimum number of subtitles in a batch; if a batch is smaller, it is merged with the previous one
- `max_batch_size` — maximum number of subtitles per batch sent to the AI server in one request

You can configure multiple models and switch between them. For example:

```
[general]
version = 0.0.2
active_model = default

[model.default]
host = 127.0.0.1
port = 1234
model = deepreinforce-ai/Orinth-1.0-9b
max_tokens = 200000
min_batch_size = 3
max_batch_size = 30

[model.fast]
host = 127.0.0.1
port = 1234
model = smaller-model
max_tokens = 8192
min_batch_size = 5
max_batch_size = 50
```

Alternatively you can use the GUI to configure the app. The settings dialog allows you to add, remove, rename models and select the active one.

Be aware that `max_tokens` depends on the model you are using and may need to be adjusted. Some models are more talkative than others and use more tokens to perform the translation. You may also need to adjust the batch size parameters (`min_batch_size` and `max_batch_size`) depending on the model used and available resources.

## Usage

### Command line

```
usage: translate.py [-h] [-f PATH] [-t TARGET_LANGUAGE] [-s SOURCE_LANGUAGE] [-o OUTPUT_FILE] [-m MODEL]

optional arguments:
  -h, --help                show this help message and exit
  -f, --subFile PATH        path to subtitle file in SRT format
  -t, --subTarget TARGET_LANGUAGE, target language of the subtitle file (default czech)
  -s, --subSource SOURCE_LANGUAGE, source language of the subtitle file (default english)
  -o, --outFile PATH        path to output file in SRT format (default translated.srt)
  -m, --model MODEL         AI model name to use (default: active model from config)
```

#### Example

```
uv run translate.py -f subtitles.srt -t czech -s english -o output.srt
```

Using a specific model:

```
uv run translate.py -f subtitles.srt -t czech -s english -o output.srt -m fast
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

The settings dialog (**File > Settings**) allows you to manage multiple AI models — add, remove, rename them, and select which one is active.

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

These settings are optimized for use with Whisper-based speech recognition.

## Audio Transcription

Transcribes audio files to SRT subtitles using OpenAI Whisper. The language is automatically detected from the filename.

### Requirements

- `openai-whisper` package (installed via `uv sync`)

### Usage

```
usage: transcribe.py [-h] -f FILE [-d DATA_DIR]

options:
  -h, --help            show this help message and exit
  -f, --file FILE       audio file path (format: video.name.lang.wav)
  -d, --data-dir        directory with language data files (default: data/)
```

### Input Format

The audio filename must follow the pattern `<video_name>.<lang>.wav`, where `<lang>` is an ISO 639-2 language code (e.g., `eng` for English, `ces` for Czech).

### Examples

```
uv run transcribe.py -f video.eng.wav
```

This produces `video.eng.srt` with timestamped subtitles.

### Output

The output is an SRT subtitle file with the same base name as the input audio, saved in the same directory. Example:

```
video.eng.wav  -->  video.eng.srt
```

The SRT file contains standard subtitle entries with index, timestamps, and transcribed text.
