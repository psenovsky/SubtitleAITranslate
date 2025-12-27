# SubtitleAITranslate

## About

Simple command line utility to quick and dirty automatictranslation of the subtitles using local AI such as OpenAI GPT-OSS using Ollama or LM-Studio.

Please note that the AI is supposed to run localy, which means that the app does not implement any kind of authentication or authorization. In other words use with caution.

## Confguration

The app is configured using a simple ini file. The file is located in the same folder as the executable. The file name is `config.ini`. The default configuration is as follows:

```
[AI]
host = 127.0.0.1
port = 1234

[general]
version = 0.0.1
```

The `host` and `port` fields are used to specify the address and port of the AI server. The AI server is expected to run on the same machine as the app. Version configuration directive is used only for informational purposes.

## Usage

```
usage: translate.py [-h] [-f PATH] [-t TARGET_LANGUAGE] [-s SOURCE_LANGUAGE] [-o OUTPUT_FILE]

optional arguments:
  -h, --help                show this help message and exit
  -f, --subFile PATH        path to subtitle file in SRT format
  -t, --subTarget TARGET_LANGUAGE, target language of the subtitle file (default english)
  -s, --subSource SOURCE_LANGUAGE, source language of the subtitle file (default czech)
  -o, --outFile PATH        path to output file in SRT format (default translated.srt)
```

### Example

```
uv run translate.py -f subtitles.srt -t czech -s english -o output.srt
```
