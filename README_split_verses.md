
# split_verses.py

A tiny command‑line tool to cut an audio file into verse segments.

## Requirements
- Python 3.9+
- `pydub`
- `openpyxl` (only required when reading Excel timestamp files)
- `ffmpeg` installed and available on your PATH

Install Python deps:
```bash
pip install -r requirements.txt
```

Install ffmpeg:
- **macOS (Homebrew):**
  ```bash
  brew install ffmpeg
  ```
- **Windows (Chocolatey):**
  ```powershell
  choco install ffmpeg
  ```
  Or with **Scoop**:
  ```powershell
  scoop install ffmpeg
  ```
- **Ubuntu/Debian:**
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```

## Quick Start (grid mode)
Example that matches your current cut (start at 00:30, 20 verses, 15s each):
```bash
python split_verses.py \
  -i "Chapter_12_-_Bhakti_Yoga_feat_Vanishree_Vijayalakshmi_KLICKAUD.mp3" \
  -o out_ch12 \
  --start 00:30 \
  --count 20 \
  --length 15 \
  --prefix "Chapter12_Verse_" \
  --zip \
  --csv out_ch12/timings.csv
```

## Custom Timestamps Mode
If you have exact verse boundaries, create a CSV with either:
```csv
start,end
00:30,00:45
00:45,01:00
...
```
**or**
```csv
start,duration
00:30,15
00:45,15
...
```

Then run:
```bash
python split_verses.py -i input.mp3 -o out --timestamps cuts.csv --prefix "Verse_" --zip --csv out/timings.csv
```

## Excel Workbook Mode
If your timestamps live in an Excel workbook (one sheet per chapter) with columns like:

| Chapter Sloka | Beginning | Ending |
|---------------|-----------|--------|
| Intro         | 0         | 0.30   |
| 12.01         | 0.30      | 0.45   |

Run:

```bash
python split_verses.py -i input.mp3 -o out --timestamps-excel chapters.xlsx --zip --csv out/timings.csv
```

Each sheet is exported to its own subdirectory (named after the sheet). File names follow the "Chapter Sloka" values (`Intro.mp3`, `12.01.mp3`, etc.).

## Options
- `--start`   : start offset (seconds or mm:ss), default `0`
- `--count`   : number of segments (grid mode), default `20`
- `--length`  : segment length (seconds or mm:ss), default `15`
- `--timestamps`: CSV of custom cuts; overrides grid
- `--prefix`  : filename prefix, default `Verse_`
- `--bitrate` : mp3 bitrate, default `192k`
- `--fade_in` : fade-in in milliseconds, default `5`
- `--fade_out`: fade-out in milliseconds, default `10`
- `--zip`     : also creates `verses.zip` in the output directory
- `--csv`     : write timings CSV to given path
- `--input-list`: text file describing audio sources used with `--timestamps-excel`

### Using `--input-list`

When you have an Excel workbook that contains timings for several audio
files, you can process them all in one run by supplying `--input-list` in
addition to `--timestamps-excel`.

Create a UTF-8 text file (for example `audio_sources.txt`) with one entry
per line. Each line can be either just a path to an audio file, applied in
order to sheets without an explicit mapping, **or** a sheet name followed by
the path, separated by a comma, tab, or `|`:

```text
# Lines starting with # are ignored
Chapter 1,chapter1.mp3
Chapter 2,chapter2.mp3
Bonus Material|extras/bonus.mp3
```

You can mix the two styles. Relative paths are resolved relative to the list
file location, so the example above looks for `chapter1.mp3` next to
`audio_sources.txt` and `extras/bonus.mp3` in the `extras` subdirectory. If a
sheet name is repeated in the list, the last entry wins.

Run the tool with:

```bash
python split_verses.py --timestamps-excel chapters.xlsx --input-list audio_sources.txt -o out
```

Each sheet uses its associated audio file while retaining all other
behaviour (ZIP/CSV output, fades, etc.).

## License
MIT — use freely in your project.
