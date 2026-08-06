import argparse
import json
import re
import subprocess
from pathlib import Path


NAME_RE = re.compile(r"^[^+]+\+[^+]+\+[^+]+\+V\d+\+.+$")


def probe(path):
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    streams = json.loads(completed.stdout).get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return video, audio


def main():
    parser = argparse.ArgumentParser(description="Validate AaddB final videos")
    parser.add_argument("product_root")
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    root = Path(args.product_root)
    files = sorted(root.rglob("*.mp4"))
    failures = []
    for path in files:
        video, audio = probe(path)
        if not NAME_RE.match(path.stem):
            failures.append(f"命名不合规: {path.name}")
        if not video:
            failures.append(f"缺少视频轨: {path}")
            continue
        size = (video.get("width"), video.get("height"))
        if size not in {(1920, 1080), (1080, 1920)}:
            failures.append(f"尺寸错误 {size}: {path}")
        if video.get("r_frame_rate") != "30/1":
            failures.append(f"帧率不是30fps: {path}")
        if not audio:
            failures.append(f"缺少音频轨: {path}")
    if args.expected is not None and len(files) != args.expected:
        failures.append(f"数量错误: expected={args.expected}, actual={len(files)}")
    print(json.dumps({"count": len(files), "ok": not failures, "failures": failures}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
