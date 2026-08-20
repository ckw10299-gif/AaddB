import argparse
import json
import subprocess
from pathlib import Path


def duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Create tail contact sheet and scene-change candidates for old-endcard review")
    parser.add_argument("video")
    parser.add_argument("output_dir")
    parser.add_argument("--tail", type=float, default=12.0)
    args = parser.parse_args()
    video = Path(args.video)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    total = duration(video)
    start = max(0.0, total - args.tail)
    sheet = output / f"{video.stem}-tail.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", str(video), "-t", str(total - start),
        "-vf", "fps=1,scale=320:-1:flags=lanczos,tile=4x3", "-frames:v", "1", str(sheet), "-loglevel", "error",
    ], check=True)
    scene = subprocess.run([
        "ffmpeg", "-ss", str(start), "-i", str(video), "-vf", "select='gt(scene,0.30)',showinfo", "-f", "null", "-",
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    candidates = []
    for line in scene.stderr.splitlines():
        if "pts_time:" in line:
            token = line.split("pts_time:", 1)[1].split()[0]
            try:
                candidates.append(round(start + float(token), 3))
            except ValueError:
                pass
    print(json.dumps({"video": str(video), "duration": total, "tail_contact_sheet": str(sheet), "scene_candidates": candidates}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
