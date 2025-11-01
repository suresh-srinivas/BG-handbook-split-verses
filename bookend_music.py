#!/usr/bin/env python3
"""bookend_music.py — Append intro/outro clips to every audio file in a directory.

Given a directory of audio files, this tool will prepend a "begin" music clip and
append an "end" music clip to each file, writing the combined result to an output
folder.  It is useful when you want consistent bookend music around already-split
verses or other short clips.

Requires: Python 3.9+, pydub, and ffmpeg installed & on PATH.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

from pydub import AudioSegment


def normalize_extensions(exts: Iterable[str]) -> List[str]:
    normalized = []
    for ext in exts:
        ext = ext.strip()
        if not ext:
            continue
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized.append(ext.lower())
    return normalized


def export_with_bitrate(segment: AudioSegment, destination: Path, bitrate: str | None) -> None:
    export_kwargs = {}
    if destination.suffix.lower() == '.mp3' and bitrate:
        export_kwargs['bitrate'] = bitrate
    segment.export(destination, format=destination.suffix.lstrip('.'), **export_kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Append begin/end music clips to every audio file in a directory."
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing source audio files (e.g., verses).",
    )
    parser.add_argument(
        "--output_dir",
        help="Directory to write processed files. Defaults to <input_dir>/bookended",
    )
    parser.add_argument(
        "--begin_music",
        default="begin-music.mp3",
        help="Path to the beginning music clip (default: begin-music.mp3)",
    )
    parser.add_argument(
        "--end_music",
        default="end-music.mp3",
        help="Path to the ending music clip (default: end-music.mp3)",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".mp3"],
        help="File extensions to include (default: .mp3). Use without dots, e.g. mp3 wav.",
    )
    parser.add_argument(
        "--prefix",
        default="bookended_",
        help="Prefix for output filenames (default: bookended_)",
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="Bitrate to use when exporting mp3 files (default: 192k)",
    )
    parser.add_argument(
        "--skip_existing",
        action="store_true",
        help="Skip files whose destination already exists.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory not found or not a directory: {input_dir}")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else input_dir / "bookended"
    output_dir.mkdir(parents=True, exist_ok=True)

    begin_music_path = Path(args.begin_music).expanduser().resolve()
    end_music_path = Path(args.end_music).expanduser().resolve()
    if not begin_music_path.is_file():
        raise SystemExit(f"Begin music file not found: {begin_music_path}")
    if not end_music_path.is_file():
        raise SystemExit(f"End music file not found: {end_music_path}")

    begin_segment = AudioSegment.from_file(begin_music_path)
    end_segment = AudioSegment.from_file(end_music_path)

    extensions = normalize_extensions(args.extensions)
    if not extensions:
        raise SystemExit("No valid extensions provided.")

    audio_files = [p for p in sorted(input_dir.iterdir()) if p.is_file() and p.suffix.lower() in extensions]
    if not audio_files:
        raise SystemExit(
            "No audio files found in input directory matching extensions: " + ", ".join(extensions)
        )

    for source_path in audio_files:
        destination_name = f"{args.prefix}{source_path.name}"
        destination_path = output_dir / destination_name
        if args.skip_existing and destination_path.exists():
            continue

        source_segment = AudioSegment.from_file(source_path)
        combined = begin_segment + source_segment + end_segment
        export_with_bitrate(combined, destination_path, args.bitrate)
        print(f"Wrote {destination_path}")

    print(f"Done. Processed {len(audio_files)} file(s). Output directory: {output_dir}")


if __name__ == "__main__":
    main()
