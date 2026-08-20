import argparse
import csv
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}


def probe(path):
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(path),
    ]
    return json.loads(subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8").stdout)


def parse(path):
    data = probe(path)
    streams = data.get("streams", [])
    video = next(s for s in streams if s.get("codec_type") == "video")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    width, height = int(video["width"]), int(video["height"])
    duration = float(data["format"]["duration"])
    match = re.search(r"V(\d+)-", path.name, re.I)
    return {
        "B面序号": f"V{match.group(1)}" if match else "",
        "B面名称": path.stem.split(";")[-1].strip(),
        "画幅": "横版" if width > height else "竖版",
        "宽": width,
        "高": height,
        "时长秒": round(duration, 3),
        "帧率": video.get("r_frame_rate", ""),
        "有音频": bool(audio),
        "文件名": path.name,
        "完整路径": str(path),
    }


def contact_sheet(path, output, duration):
    interval = max(duration / 6.0, 0.1)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(path), "-vf", f"fps=1/{interval:.6f},scale=320:-1:flags=lanczos,tile=3x2",
        "-frames:v", "1", str(output), "-loglevel", "error",
    ], check=True)


def inspect_one(path, contact_dir):
    row = parse(path)
    contact = contact_dir / f"{path.stem}.jpg"
    contact_sheet(path, contact, row["时长秒"])
    row["抽帧联系表"] = str(contact)
    return row


def main():
    parser = argparse.ArgumentParser(description="Build reusable B-side technical and contact-sheet cache")
    parser.add_argument("b_root")
    parser.add_argument("output_dir")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    output = Path(args.output_dir)
    contacts = output / "contact_sheets"
    contacts.mkdir(parents=True, exist_ok=True)
    videos = sorted(p for p in Path(args.b_root).rglob("*") if p.suffix.lower() in VIDEO_EXTENSIONS)
    rows, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(inspect_one, path, contacts): path for path in videos}
        for job in as_completed(jobs):
            try:
                rows.append(job.result())
            except Exception as exc:
                failures.append({"path": str(jobs[job]), "error": str(exc)})
    rows.sort(key=lambda x: (x["B面序号"], x["画幅"], x["文件名"]))
    output.mkdir(parents=True, exist_ok=True)
    (output / "b_analysis.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if rows:
        with (output / "b_analysis.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"videos": len(videos), "success": len(rows), "failures": failures}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
