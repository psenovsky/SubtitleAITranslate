import json  # JSON parsing
import re  # regular expressions
import urllib.request  # make HTTP requests

from tqdm import tqdm  # progress bar


def translate_subtitles(subtitles, language_from, language_to, config):
    """
    Translate subtitles in SRT format from one language to another using LM‑Studio.

    Parameters:
        subtitles (str): The entire SRT file as a string.
        language_from (str): Source language code (e.g., "en").
        language_to   (str): Target language code (e.g., "es").
        config (dict): Configuration dictionary.

    Returns:
        str: Translated SRT content.
    """

    # Split the SRT into blocks separated by double newlines
    blocks = re.split(r"\n\s*\n", subtitles.strip())
    translated_blocks = []

    for block in tqdm(blocks, desc="Translating Subtitles", unit="block"):
        # for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            # Not a valid subtitle block; keep as is
            translated_blocks.append(block)
            continue

        # First line: index, second: timestamp, rest: text
        index = lines[0]
        timestamps = lines[1]
        text_lines = lines[2:]

        # Join multiple text lines into one string for translation
        original_text = "\n".join(text_lines)

        # Prepare the prompt for LM‑Studio
        prompt = (
            f"Translate the following subtitle from {language_from} to {language_to}:\n\n"
            f"{original_text}"
        )

        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.3,
        }

        # LM‑Studio endpoint (adjust if needed)
        ip = config["AI"]["host"]
        port = config["AI"]["port"]
        url = f"http://{ip}:{port}/v1/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                translated_text = result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # Fallback: keep original text if translation fails
            translated_text = original_text

        # Reconstruct the block with translated text
        translated_block = "\n".join([index, timestamps] + translated_text.splitlines())
        translated_blocks.append(translated_block)

    return "\n\n".join(translated_blocks)
