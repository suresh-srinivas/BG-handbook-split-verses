
#!/usr/bin/env python3
"""
split_verses.py — Cut an audio file into fixed-length "verses" (or custom timestamps).

Features:
  - Start at an offset (e.g., 30s) and slice N segments of length L.
  - Optional CSV with timings.
  - Optional fades to avoid clicks.
  - Optional ZIP of outputs.
  - Alternative mode: provide a timestamps CSV to define exact cuts.

Requires: Python 3.9+, pydub, and ffmpeg installed & on PATH.
"""
import argparse
import csv
import os
from typing import List, Tuple, Optional
from pydub import AudioSegment
import zipfile

def parse_time(s: str) -> int:
    """
    Parse time like "75" (seconds), "01:15", or "01:15.250" into milliseconds.
    """
    s = s.strip()
    if ':' not in s:
        # seconds (possibly float)
        sec = float(s)
        return int(round(sec * 1000))
    parts = s.split(':')
    if len(parts) == 2:
        mm, ss = parts
        return int(round((int(mm) * 60 + float(ss)) * 1000))
    elif len(parts) == 3:
        hh, mm, ss = parts
        total_sec = int(hh) * 3600 + int(mm) * 60 + float(ss)
        return int(round(total_sec * 1000))
    else:
        raise ValueError(f"Unrecognized time format: {s}")

def mmss(ms: int) -> str:
    s = int(round(ms/1000))
    m = s // 60
    sec = s % 60
    return f"{m:02d}:{sec:02d}"

def grid_cuts(start_ms: int, count: int, length_ms: int, total_ms: int) -> List[Tuple[int, int]]:
    cuts = []
    for i in range(count):
        st = start_ms + i * length_ms
        en = st + length_ms
        st = max(0, min(st, total_ms))
        en = max(0, min(en, total_ms))
        if en <= st:
            break
        cuts.append((st, en))
    return cuts

def load_timestamps_csv(path: str, total_ms: int) -> List[Tuple[int,int]]:
    """
    CSV with either headers or not. Expect either:
      start,end
    or
      start,duration
    Time formats accept seconds or mm:ss(.ms)
    """
    cuts = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)
    # try to detect header
    def normalize_header(cell: str) -> str:
        return ''.join(ch for ch in cell.lower() if ch.isalnum())

    def find_column(header_norm: List[str], keywords: Tuple[str, ...]) -> Optional[int]:
        for idx, norm in enumerate(header_norm):
            for kw in keywords:
                if norm == kw or norm.startswith(kw):
                    return idx
        return None

    header_raw = [c.strip() for c in rows[0]] if rows else []
    header_norm = [normalize_header(c) for c in header_raw]
    idx_start: Optional[int] = None
    idx_end: Optional[int] = None
    idx_dur: Optional[int] = None

    def row_looks_like_header(row: List[str]) -> bool:
        return any(any(ch.isalpha() for ch in cell) for cell in row)

    start_row = 0
    if header_raw and row_looks_like_header(header_raw):
        start_row = 1
        idx_start = find_column(header_norm, ("start", "begin"))
        idx_end = find_column(header_norm, ("end", "stop", "finish"))
        idx_dur = find_column(header_norm, ("duration", "length", "dur"))

    for r in rows[start_row:]:
        row = [cell.strip() for cell in r]
        if not row or all(not cell for cell in row):
            continue
        use_end = False
        start_s: Optional[str] = None
        second: Optional[str] = None

        if idx_start is not None and idx_start < len(row) and row[idx_start]:
            start_s = row[idx_start]
            if idx_end is not None and idx_end < len(row) and row[idx_end]:
                second = row[idx_end]
                use_end = True
            elif idx_dur is not None and idx_dur < len(row) and row[idx_dur]:
                second = row[idx_dur]
        if start_s is None or second is None:
            # fall back to the first two populated columns (legacy behaviour)
            populated = [cell for cell in row if cell]
            if len(populated) < 2:
                raise ValueError("Timestamps CSV needs at least 2 columns (start,end or start,duration).")
            start_s, second = populated[0], populated[1]
            use_end = False

        st = parse_time(start_s)
        if use_end:
            en = parse_time(second)
        else:
            dur = parse_time(second)
            en = st + dur

        # clamp
        st = max(0, min(st, total_ms))
        en = max(0, min(en, total_ms))
        if en > st:
            cuts.append((st, en))
    return cuts

def main():
    ap = argparse.ArgumentParser(description="Split audio into verses by grid or timestamps.")
    ap.add_argument("-i","--input", required=True, help="Input audio file (mp3/wav/etc.)")
    ap.add_argument("-o","--output", default="verses_out", help="Output directory")
    ap.add_argument("--start", default="0", help='Start offset (seconds or mm:ss), default 0')
    ap.add_argument("--count", type=int, default=20, help="Number of verses to cut (grid mode)")
    ap.add_argument("--length", default="15", help="Verse length (seconds or mm:ss) in grid mode")
    ap.add_argument("--timestamps", help="CSV of custom cuts: start,end or start,duration (overrides grid)")
    ap.add_argument("--prefix", default="Verse_", help="Filename prefix, default Verse_")
    ap.add_argument("--bitrate", default="192k", help="Output bitrate for mp3, default 192k")
    ap.add_argument("--fade_in", type=int, default=5, help="Fade in ms, default 5")
    ap.add_argument("--fade_out", type=int, default=10, help="Fade out ms, default 10")
    ap.add_argument("--zip", dest="make_zip", action="store_true", help="Also produce a ZIP of outputs")
    ap.add_argument("--csv", dest="csv_out", help="Write a timings CSV to this path")
    args = ap.parse_args()

    os.makedirs(args.output, exist_ok=True)

    audio = AudioSegment.from_file(args.input)
    total_ms = len(audio)

    if args.timestamps:
        cuts = load_timestamps_csv(args.timestamps, total_ms)
        if not cuts:
            raise SystemExit("No valid cuts parsed from timestamps CSV.")
    else:
        start_ms = parse_time(args.start)
        length_ms = parse_time(args.length)
        cuts = grid_cuts(start_ms, args.count, length_ms, total_ms)
        if not cuts:
            raise SystemExit("No valid cuts produced by grid. Check --start/--count/--length.")

    rows = []
    export_paths = []
    for idx, (st, en) in enumerate(cuts, start=1):
        seg = audio[st:en].fade_in(args.fade_in).fade_out(args.fade_out)
        fname = f"{args.prefix}{idx:02d}.mp3"
        fpath = os.path.join(args.output, fname)
        seg.export(fpath, format="mp3", bitrate=args.bitrate)
        export_paths.append(fpath)
        rows.append((idx, mmss(st), mmss(en), round(len(seg)/1000,3), fname))

    if args.csv_out:
        with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Verse","Start","End","Duration(s)","File"])
            for r in rows:
                w.writerow(r)

    if args.make_zip:
        zip_path = os.path.join(args.output, "verses.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in export_paths:
                zf.write(p, arcname=os.path.basename(p))

    print(f"Done. Wrote {len(export_paths)} files to: {args.output}")
    if args.make_zip:
        print(f"ZIP: {os.path.join(args.output, 'verses.zip')}")
    if args.csv_out:
        print(f"CSV: {args.csv_out}")

if __name__ == "__main__":
    main()
