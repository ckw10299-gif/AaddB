import argparse
import json
import re
from pathlib import Path


DISCLAIMER = "广告创意仅供参考，实际以游戏内为准"


def ass_time(seconds):
    seconds = max(0.0, float(seconds))
    return f"{int(seconds // 3600)}:{int(seconds % 3600 // 60):02d}:{seconds % 60:05.2f}"


def clean_text(text):
    text = str(text).replace("\n", " ").replace("?", "？")
    return re.sub(r"[^\w\u4e00-\u9fff？]", "", text, flags=re.UNICODE).strip()


def events(data, max_chars=14, max_duration=2.8):
    result = []
    for segment in data.get("segments", []):
        words = [w for w in (segment.get("words") or []) if w.get("word") and w.get("start") is not None and w.get("end") is not None]
        if not words:
            text = clean_text(segment.get("text", ""))
            if text:
                result.append((float(segment["start"]), float(segment["end"]), text))
            continue
        group = []
        for word in words:
            if group and float(word["start"]) - float(group[-1]["end"]) > 0.45:
                result.append((float(group[0]["start"]), float(group[-1]["end"]), clean_text("".join(x["word"] for x in group))))
                group = []
            group.append(word)
            text = clean_text("".join(x["word"] for x in group))
            if len(text) >= max_chars or float(group[-1]["end"]) - float(group[0]["start"]) >= max_duration or text.endswith("？"):
                result.append((float(group[0]["start"]), float(group[-1]["end"]), text))
                group = []
        if group:
            result.append((float(group[0]["start"]), float(group[-1]["end"]), clean_text("".join(x["word"] for x in group))))
    return [item for item in result if item[2]]


def main():
    parser = argparse.ArgumentParser(description="Generate reviewed ASS subtitles for A-side")
    parser.add_argument("transcript_json")
    parser.add_argument("output_ass")
    parser.add_argument("--orientation", choices=("vertical", "horizontal"), required=True)
    parser.add_argument("--a-duration", type=float, required=True)
    parser.add_argument("--font", default="Microsoft YaHei")
    parser.add_argument("--disclaimer", default=DISCLAIMER)
    args = parser.parse_args()

    data = json.loads(Path(args.transcript_json).read_text(encoding="utf-8-sig"))
    subtitle_events = events(data)
    if not subtitle_events:
        raise ValueError("Transcript contains no usable subtitle events")

    if args.orientation == "vertical":
        width, height, font_size, margin_v, note_size = 1080, 1920, 68, 290, 24
    else:
        width, height, font_size, margin_v, note_size = 1920, 1080, 54, 135, 20
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Subtitle,{args.font},{font_size},&H00FFFFFF,&H000000FF,&H00151515,&H50000000,-1,0,0,0,100,100,0,0,1,3,1,2,55,55,{margin_v},1
Style: Disclaimer,{args.font},{note_size},&H00FFFFFF,&H000000FF,&H00151515,&H50000000,0,0,0,0,100,100,0,0,1,1,0,3,20,24,18,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    lines = [header]
    for start, end, text in subtitle_events:
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(max(end, start + 0.08))},Subtitle,,0,0,0,,{text}\n")
    lines.append(f"Dialogue: 1,0:00:00.00,{ass_time(args.a_duration)},Disclaimer,,0,0,0,,{args.disclaimer}\n")
    Path(args.output_ass).write_text("".join(lines), encoding="utf-8-sig")


if __name__ == "__main__":
    main()
