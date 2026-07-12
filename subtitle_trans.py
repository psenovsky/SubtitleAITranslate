import json  # JSON parsing
import re  # regular expressions
import urllib.request  # make HTTP requests
import urllib.error  # HTTP error handling

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
    stats = {"total": len(blocks), "translated": 0, "skipped": 0, "empty": 0, "errors": 0}
    warnings = []

    ip = config["AI"]["host"]
    port = config["AI"]["port"]
    url = f"http://{ip}:{port}/v1/chat/completions"

    for block_idx, block in enumerate(tqdm(blocks, desc="Translating Subtitles", unit="block"), 1):
        lines = block.splitlines()
        if len(lines) < 3:
            # Not a valid subtitle block; keep as is
            translated_blocks.append(block)
            stats["skipped"] += 1
            continue

        # First line: index, second: timestamp, rest: text
        index = lines[0]
        timestamps = lines[1]
        text_lines = lines[2:]

        # Join multiple text lines into one string for translation
        original_text = "\n".join(text_lines)

        # Prepare the prompt for LM‑Studio
        system_message = (
            "You are a professional subtitle translator. Your task is to translate subtitle text while preserving all formatting. "
            "Rules:\n"
            "1. Preserve ALL HTML tags exactly as they appear (e.g., <i>, </i>, <b>, </b>, <font>, etc.). "
            "Translate only the text content between tags, never modify the tags themselves.\n"
            "2. Preserve escape sequences exactly as they appear (e.g., \\n, \\t). Do not convert them to actual characters.\n"
            "3. Do not add quotation marks in the translation unless they are present in the original text.\n"
            "4. Return ONLY the translated text, nothing else. No explanations, no quotes around the result.\n"
            "5. Maintain the same number of lines as the original text."
        )

        user_message = (
            f"Translate from {language_from} to {language_to}:\n\n{original_text}"
        )

        payload = {
            "model": config["AI"]["model"],
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 5000,
            "temperature": 0.3,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )

        translated_text = None
        finish_reason = None
        usage = None
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())

            # Validate response structure
            if "choices" not in result or not result["choices"]:
                warnings.append(f"⚠ Block {block_idx} ({index}): No choices in response")
                stats["errors"] += 1
            elif "message" not in result["choices"][0]:
                warnings.append(f"⚠ Block {block_idx} ({index}): No message in response choice")
                stats["errors"] += 1
            else:
                translated_text = result["choices"][0]["message"]["content"]
                finish_reason = result["choices"][0].get("finish_reason")
                usage = result.get("usage")

        except urllib.error.URLError as e:
            warnings.append(f"⚠ Block {block_idx} ({index}): Connection error - {e}")
            stats["errors"] += 1
        except json.JSONDecodeError as e:
            warnings.append(f"⚠ Block {block_idx} ({index}): Invalid JSON response - {e}")
            stats["errors"] += 1
        except KeyError as e:
            warnings.append(f"⚠ Block {block_idx} ({index}): Missing key in response - {e}")
            stats["errors"] += 1
        except Exception as e:
            warnings.append(f"⚠ Block {block_idx} ({index}): Unexpected error - {type(e).__name__}: {e}")
            stats["errors"] += 1

        # Process the translated text
        if translated_text is not None:
            translated_text = translated_text.strip()

            # Check for empty response
            if not translated_text:
                detail = f"finish_reason={finish_reason}"
                if usage:
                    detail += f", tokens(in={usage.get('prompt_tokens', '?')}, out={usage.get('completion_tokens', '?')})"
                warnings.append(f"⚠ Block {block_idx} ({index}): Empty translation, keeping original [{detail}]")
                translated_text = original_text
                stats["empty"] += 1
            else:
                stats["translated"] += 1

                # Warn if response has significantly more lines than original
                original_line_count = len(text_lines)
                translated_line_count = len(translated_text.splitlines())
                if translated_line_count > original_line_count + 2:
                    warnings.append(f"⚠ Block {block_idx} ({index}): Response has {translated_line_count} lines, expected ~{original_line_count}")
        else:
            # Translation failed, keep original
            translated_text = original_text
            stats["errors"] += 1

        # Reconstruct the block with translated text
        translated_block = "\n".join([index, timestamps] + translated_text.splitlines())
        translated_blocks.append(translated_block)

    # Print warnings then summary
    if warnings:
        print()
        for w in warnings:
            print(w)
    print(f"\nTranslation complete: {stats['translated']} translated, {stats['empty']} empty (kept original), {stats['skipped']} skipped, {stats['errors']} errors")

    return "\n\n".join(translated_blocks)
