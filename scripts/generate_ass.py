import argparse
import json
from pathlib import Path


DISCLAIMER = "广告创意仅供参考，实际以游戏内为准"


def ass_time(seconds):
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600 // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def clean_text(text):
    return str(text).replace("\n", "\\N").replace("{", "（").replace("}", "）").strip()


def load_events(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    events = []
    for segment in data.get("segments", []):
        text = clean_text(segment.get("text", ""))
        if not text:
            continue
        start = float(segment["start"])
        end = max(start + 0.08, float(segment["end"]))
        events.append((start, end, text))
    if not events:
        raise ValueError("转写 JSON 中没有可用字幕事件")
    return data, events


def main():
    parser = argparse.ArgumentParser(description="Generate reviewed A-side ASS subtitles")
    parser.add_argument("transcript_json")
    parser.add_argument("output_ass")
    parser.add_argument("--orientation", choices=("vertical", "horizontal"), required=True)
    parser.add_argument("--a-duration", type=float, required=True)
    parser.add_argument("--font", default="Microsoft YaHei")
    parser.add_argument("--disclaimer", default=DISCLAIMER)
    args = parser.parse_args()

    _, events = load_events(args.transcript_json)
    if args.orientation == "vertical":
        width, height, font_size, margin_v, note_size = 1080, 1920, 90, 610, 25
        note_right, note_bottom = 24, 18
    else:
        width, height, font_size, margin_v, note_size = 1920, 1080, 56, 330, 18
        note_right, note_bottom = 32, 20

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{args.font},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,{margin_v},1
Style: Disclaimer,{args.font},{note_size},&HCCFFFFFF,&H000000FF,&H99000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,3,10,{note_right},{note_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for start, end, text in events:
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Main,,0,0,0,,{text}\n")
    if args.disclaimer:
        lines.append(
            f"Dialogue: 1,{ass_time(0)},{ass_time(args.a_duration)},Disclaimer,,0,0,0,,{clean_text(args.disclaimer)}\n"
        )
    Path(args.output_ass).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_ass).write_text("".join(lines), encoding="utf-8-sig")


if __name__ == "__main__":
    main()
