import json
import re
import urllib.request
import urllib.error
from dataclasses import dataclass

from tqdm import tqdm


@dataclass
class Subtitle:
    id: int
    timestamps: str
    text: str


def parse_srt(subtitles: str) -> list[Subtitle]:
    blocks = re.split(r"\n\s*\n", subtitles.strip())
    result = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        try:
            sub_id = int(lines[0])
        except ValueError:
            continue
        timestamps = lines[1]
        text = "\n".join(lines[2:])
        result.append(Subtitle(id=sub_id, timestamps=timestamps, text=text))
    return result


def to_srt(subtitles: list[Subtitle]) -> str:
    blocks = []
    for sub in subtitles:
        block = f"{sub.id}\n{sub.timestamps}\n{sub.text}"
        blocks.append(block)
    return "\n\n".join(blocks)


def estimate_tokens(text: str) -> int:
    return len(text) // 4 + 1


def query_max_tokens(config) -> int:
    ip = config["AI"]["host"]
    port = config["AI"]["port"]
    url = f"http://{ip}:{port}/v1/models"
    configured_max = int(config["AI"]["max_tokens"])
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
        if "data" in result and result["data"]:
            model_info = result["data"][0]
            for key in ["max_context_length", "max_tokens", "context_length"]:
                if key in model_info:
                    return int(model_info[key])
    except Exception:
        pass
    return configured_max


def batch_subtitles(subtitles: list[Subtitle], max_tokens: int) -> list[list[Subtitle]]:
    available_tokens = max_tokens - 500
    batches = []
    current_batch = []
    current_tokens = 0
    min_batch_size = 3
    max_batch_size = 50

    for sub in subtitles:
        sub_tokens = estimate_tokens(sub.text)
        if current_batch and (current_tokens + sub_tokens > available_tokens or len(current_batch) >= max_batch_size):
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(sub)
        current_tokens += sub_tokens

    if current_batch:
        if batches and len(current_batch) < min_batch_size:
            batches[-1].extend(current_batch)
        else:
            batches.append(current_batch)

    return batches


def _build_batch_prompt(batch: list[Subtitle], language_from: str, language_to: str) -> str:
    parts = [
        f"Translate these subtitles from {language_from} to {language_to}.",
        "Each subtitle has a number in brackets, timestamps, and text.",
        "Return translations in the EXACT same format with the same numbers.",
        "Preserve all HTML tags (e.g., <i>, </i>) and escape sequences (e.g., \\n).",
        "Return ONLY the translations, no explanations.\n",
    ]
    for sub in batch:
        parts.append(f"[{sub.id}]\n{sub.timestamps}\n{sub.text}\n")
    return "\n".join(parts)


SYSTEM_MESSAGE = """You are a professional subtitle translator. Your task is to translate subtitle text while preserving all formatting.

Rules:
1. Preserve ALL HTML tags exactly as they appear (e.g., <i>, </i>, <b>, </b>, <font>, etc.). Translate only the text content between tags, never modify the tags themselves.
2. Preserve escape sequences exactly as they appear (e.g., \\n, \\t). Do not convert them to actual characters.
3. Do not add quotation marks in the translation unless they are present in the original text.
4. Return ONLY the translated text, nothing else. No explanations, no quotes around the result.
5. Maintain the same number of lines as the original text.
6. Each subtitle block is numbered in brackets [N]. Preserve these numbers exactly in your response.
7. Preserve timestamp lines exactly as they appear (e.g., 00:00:01,500 --> 00:00:04,200)."""


def translate_batch(batch: list[Subtitle], language_from: str, language_to: str, config: dict) -> str | None:
    ip = config["AI"]["host"]
    port = config["AI"]["port"]
    url = f"http://{ip}:{port}/v1/chat/completions"

    user_message = _build_batch_prompt(batch, language_from, language_to)

    payload = {
        "model": config["AI"]["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": int(config["AI"]["max_tokens"]),
        "temperature": 0.3,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
        if "choices" not in result or not result["choices"]:
            return None
        if "message" not in result["choices"][0]:
            return None
        return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def parse_batch_response(response_text: str, original_batch: list[Subtitle]) -> list[Subtitle] | None:
    pattern = r"\[(\d+)\]\s*\n(\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3})\s*\n(.+?)(?=\n\[\d+\]|\Z)"
    matches = re.findall(pattern, response_text, re.DOTALL)

    if not matches:
        return None

    translated_map = {}
    for match in matches:
        sub_id = int(match[0])
        timestamps = match[1].strip()
        text = match[2].strip()
        translated_map[sub_id] = Subtitle(id=sub_id, timestamps=timestamps, text=text)

    result = []
    for original in original_batch:
        if original.id not in translated_map:
            return None
        translated = translated_map[original.id]
        result.append(Subtitle(
            id=original.id,
            timestamps=original.timestamps,
            text=translated.text,
        ))

    return result


def translate_single(sub: Subtitle, language_from: str, language_to: str, config: dict) -> Subtitle:
    ip = config["AI"]["host"]
    port = config["AI"]["port"]
    url = f"http://{ip}:{port}/v1/chat/completions"

    user_message = f"Translate from {language_from} to {language_to}:\n\n{sub.text}"

    payload = {
        "model": config["AI"]["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": int(config["AI"]["max_tokens"]),
        "temperature": 0.3,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
        if "choices" in result and result["choices"] and "message" in result["choices"][0]:
            translated_text = result["choices"][0]["message"]["content"].strip()
            if translated_text:
                return Subtitle(id=sub.id, timestamps=sub.timestamps, text=translated_text)
    except Exception:
        pass

    return sub


def translate_subtitles(subtitles, language_from, language_to, config):
    all_subs = parse_srt(subtitles)
    if not all_subs:
        return subtitles

    max_tokens = query_max_tokens(config)
    batches = batch_subtitles(all_subs, max_tokens)

    result = []
    stats = {"total": len(all_subs), "translated": 0, "empty": 0, "errors": 0, "batches": len(batches)}
    tokens = {"prompt": 0, "completion": 0, "total": 0}
    warnings = []

    pbar = tqdm(total=len(all_subs), desc="Translating subtitles", unit="sub")

    for batch_idx, batch in enumerate(batches, 1):
        response_text = translate_batch(batch, language_from, language_to, config)

        if response_text is not None:
            translated_batch = parse_batch_response(response_text, batch)
        else:
            translated_batch = None

        if translated_batch is not None:
            for original, translated in zip(batch, translated_batch):
                if translated.text and translated.text != original.text:
                    stats["translated"] += 1
                elif not translated.text:
                    stats["empty"] += 1
                    translated = original
                result.append(translated)
            pbar.update(len(batch))
        else:
            warnings.append(f"⚠ Batch {batch_idx} failed, falling back to individual translation")
            for sub in batch:
                translated = translate_single(sub, language_from, language_to, config)
                if translated.text and translated.text != sub.text:
                    stats["translated"] += 1
                else:
                    stats["empty"] += 1
                result.append(translated)
                pbar.update(1)

    pbar.close()

    if warnings:
        print()
        for w in warnings:
            print(w)

    print(f"\nTranslation complete: {stats['translated']} translated, {stats['empty']} kept original, {stats['errors']} errors")
    print(f"Processed in {stats['batches']} batches ({len(all_subs)} subtitles)")

    return to_srt(result)
