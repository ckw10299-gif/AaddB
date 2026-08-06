import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def python(script, *args):
    run(sys.executable, HERE / script, *args)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def last_word_start(transcript):
    words = [word for segment in transcript.get("segments", []) for word in (segment.get("words") or [])]
    if not words:
        raise ValueError("没有词级时间戳，无法可靠确定转场点")
    return float(words[-1]["start"])


def a_name(path, requester):
    name = path.stem.strip()
    name = re.sub(r"(?:\s*[-_]?\s*)(横版|竖版|horizontal|vertical)$", "", name, flags=re.I).strip()
    name = re.sub(rf"(?:\s*[-_]?\s*){re.escape(requester)}$", "", name, flags=re.I).strip()
    if not name:
        raise ValueError(f"无法提取A面名称: {path.name}")
    return name


def safe_name(text):
    return re.sub(r'[<>:"/\\|?*]', "_", text).strip(" .")


def main():
    parser = argparse.ArgumentParser(description="Complete AaddB workflow")
    parser.add_argument("root")
    parser.add_argument("--a-requester", required=True)
    parser.add_argument("--phase", choices=("prepare", "render", "all"), default="prepare")
    parser.add_argument("--approve-subtitles", action="store_true")
    parser.add_argument("--model", default="large-v3-turbo")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    work = root / ".aaddb-work"
    work.mkdir(exist_ok=True)
    inventory_path = work / "inventory.json"
    with inventory_path.open("w", encoding="utf-8") as handle:
        subprocess.run(
            [sys.executable, str(HERE / "inventory.py"), str(root), "--a-requester", args.a_requester],
            check=True, stdout=handle, text=True, encoding="utf-8",
        )
    inventory = load_json(inventory_path)
    a_records = [x for x in inventory["files"] if x["role"] == "A" and x["orientation"] != "ambiguous"]
    b_records = [x for x in inventory["files"] if x["role"] == "B" and not x.get("duplicate_of") and x["orientation"] != "ambiguous"]
    glossary = root / "专有名词库.txt"

    prepared = []
    for record in a_records:
        source = Path(record["path"])
        key = safe_name(source.stem)
        transcript = work / f"{key}.json"
        ass = work / f"{key}.ass"
        preview = work / f"{key}-字幕预览.mp4"
        if not transcript.exists():
            command = [source, transcript, "--model", args.model]
            if glossary.exists():
                command += ["--glossary", glossary]
            python("transcribe.py", *command)
        python(
            "generate_ass.py", transcript, ass,
            "--orientation", record["orientation"], "--a-duration", record["duration"],
        )
        width, height = ((1080, 1920) if record["orientation"] == "vertical" else (1920, 1080))
        ass_filter = ass.resolve().as_posix().replace(":", r"\:")
        run(
            "ffmpeg", "-y", "-i", source, "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30,ass='{ass_filter}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "aac", "-b:a", "192k", preview,
        )
        prepared.append((record, source, transcript, ass, preview))

    manifest = {
        "instruction": "逐条审核字幕预览；如有错误，修改对应JSON的segments文本/时间后重新prepare。确认无误才能render。",
        "items": [{"a": str(x[1]), "transcript": str(x[2]), "ass": str(x[3]), "preview": str(x[4])} for x in prepared],
    }
    (work / "review-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.phase == "prepare":
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    if not args.approve_subtitles:
        raise SystemExit("拒绝批量渲染：请先审核所有字幕预览，再加 --approve-subtitles")

    collisions = {}
    planned = []
    for a_record, source, transcript_path, ass, _ in prepared:
        transcript = load_json(transcript_path)
        offset = last_word_start(transcript)
        for b in b_records:
            if b["orientation"] != a_record["orientation"]:
                continue
            base = safe_name(
                f"{args.a_requester}+{b['requester']}+{a_name(source, args.a_requester)}+{b['sequence']}+{b['name']}"
            )
            category = b["category"]
            key = (category, base)
            collisions[key] = collisions.get(key, 0) + 1
            planned.append((a_record, source, ass, offset, b, base))

    outputs = []
    for a_record, source, ass, offset, b, base in planned:
        if collisions[(b["category"], base)] > 1:
            base += "横版" if a_record["orientation"] == "horizontal" else "竖版"
        out_dir = root / "成品" / b["category"]
        out_dir.mkdir(parents=True, exist_ok=True)
        output = out_dir / f"{base}.mp4"
        python(
            "render_transition.py", source, b["path"], ass, output,
            "--orientation", a_record["orientation"],
            "--a-duration", a_record["duration"], "--transition-offset", offset,
        )
        outputs.append(str(output))
    python("qa.py", root / "成品", "--expected", len(outputs))


if __name__ == "__main__":
    main()
