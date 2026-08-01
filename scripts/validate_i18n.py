#!/usr/bin/env python3
"""Validate that every LiteLLM UI dictionary has the same safe structure."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DICTIONARY_DIR = ROOT / "zhtw"
DICTIONARIES = (
    "dict.json",
    "dict.en.json",
    "dict.zh-CN.json",
    "dict.ja.json",
    "dict.ko.json",
)

PRESERVED_PATTERNS = {
    "dollar amount or numbered placeholder": re.compile(r"\$\d+(?:\.\d+)?"),
    "template placeholder": re.compile(
        r"\$\{[^{}]+\}|\{\{[^{}]+\}\}|"
        r"(?<!\{)\{[A-Za-z_][A-Za-z0-9_.:-]*\}(?!\})|"
        r"%\([^)]+\)[#0 +\-]?\d*(?:\.\d+)?[A-Za-z]|(?<!%)%[sdif]"
    ),
    "URL": re.compile(r"https?://[^\s<>\"']+"),
    "HTML tag": re.compile(r"</?[A-Za-z][^>]*>"),
    "CLI flag": re.compile(r"(?<!\w)--[A-Za-z0-9][A-Za-z0-9_-]*"),
    "environment variable": re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b"),
    "program identifier": re.compile(
        r"(?<![A-Za-z0-9_])(?:[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|"
        r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+)(?![A-Za-z0-9_])"
    ),
}
INVISIBLE_CHARACTERS = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")


class JsonObjectPairs(list):
    """Distinguish a decoded JSON object from a top-level JSON array."""


def load_pairs(path: Path) -> list[tuple[str, str]]:
    data = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=JsonObjectPairs
    )
    if not isinstance(data, JsonObjectPairs):
        raise ValueError("top-level JSON value must be an object")
    return list(data)


def validate() -> list[str]:
    errors: list[str] = []
    dictionaries: dict[str, list[tuple[str, str]]] = {}

    for filename in DICTIONARIES:
        path = DICTIONARY_DIR / filename
        try:
            pairs = load_pairs(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{filename}: cannot load dictionary: {exc}")
            continue

        keys = [key for key, _ in pairs]
        duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
        if duplicates:
            errors.append(f"{filename}: duplicate keys: {duplicates[:5]!r}")
        if not all(
            isinstance(key, str) and isinstance(value, str) for key, value in pairs
        ):
            errors.append(f"{filename}: every key and value must be a string")
        dictionaries[filename] = pairs

    if "dict.json" not in dictionaries:
        return errors

    source_pairs = dictionaries["dict.json"]
    source_keys = [key for key, _ in source_pairs]
    for filename, pairs in dictionaries.items():
        keys = [key for key, _ in pairs]
        if keys != source_keys:
            mismatch = next(
                (
                    index
                    for index, pair in enumerate(zip(source_keys, keys))
                    if pair[0] != pair[1]
                ),
                min(len(source_keys), len(keys)),
            )
            errors.append(
                f"{filename}: key set/order differs from dict.json at index {mismatch}"
            )

    english_pairs = dictionaries.get("dict.en.json", [])
    for key, value in english_pairs:
        if key != value:
            errors.append(f"dict.en.json: value must equal key: {key!r}")
            if len(errors) >= 20:
                break

    for filename, pairs in dictionaries.items():
        if filename == "dict.json":
            continue
        for key, value in pairs:
            for label, pattern in PRESERVED_PATTERNS.items():
                source_tokens = Counter(pattern.findall(key))
                translated_tokens = Counter(pattern.findall(value))
                if source_tokens != translated_tokens:
                    errors.append(
                        f"{filename}: changed {label} in {key!r}: "
                        f"{dict(source_tokens)!r} != {dict(translated_tokens)!r}"
                    )
            if INVISIBLE_CHARACTERS.search(value):
                errors.append(f"{filename}: invisible control character in {key!r}")
            if bool(key[:1].isspace()) != bool(value[:1].isspace()):
                errors.append(f"{filename}: changed leading whitespace in {key!r}")
            if bool(key[-1:].isspace()) != bool(value[-1:].isspace()):
                errors.append(f"{filename}: changed trailing whitespace in {key!r}")
            if "\ufffd" in value:
                errors.append(f"{filename}: replacement character in {key!r}")
            if unicodedata.normalize("NFC", value) != value:
                errors.append(f"{filename}: value is not NFC-normalized: {key!r}")

    return errors


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")

    errors = validate()
    if errors:
        print(f"i18n validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    count = len(load_pairs(DICTIONARY_DIR / "dict.json"))
    print(
        f"i18n validation passed: {len(DICTIONARIES)} dictionaries, {count} keys each"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
