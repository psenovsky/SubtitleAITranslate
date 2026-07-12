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
max_tokens = 5000

[general]
version = 0.0.2
```

The configuration directives are:

- `host` — address of the AI server (expected to run locally)
- `port` — port of the AI server
- `model` — the LLM model name to use for translation
- `max_tokens` — maximum number of tokens in the AI response
- `version` — informational, version of the app used in the CLI help output

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
