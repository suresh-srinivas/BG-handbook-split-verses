
# split_verses.py

A tiny command‑line tool to cut an audio file into verse segments.

## Requirements
- Python 3.9+
- `pydub`
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

## Add Bookend Music to Many Files

If you already have a folder of clips (e.g., after running `split_verses.py`), use
`bookend_music.py` to wrap each file with intro/outro music:

```bash
python bookend_music.py verses_out --begin_music begin-music.mp3 --end_music end-music.mp3
```

By default it writes the results to `verses_out/bookended` and only processes `.mp3`
files. See `python bookend_music.py --help` for flags to change the output directory,
supported extensions, filename prefix, or bitrate.

## License
MIT — use freely in your project.
