import argparse
import json
import re
import subprocess
from pathlib import Path


NAME_RE = re.compile(r"^[^+]+\+V\d+\+[^+]+\+(横|竖)(包框)?$")


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="Validate AaddB output videos")
    parser.add_argument("product_root")
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    root = Path(args.product_root)
    category_dirs = [root / name for name in ("预约", "体验") if (root / name).is_dir()]
    files = sorted(path for folder in category_dirs for path in folder.glob("*.mp4")) if category_dirs else sorted(root.rglob("*.mp4"))
    failures = []
    for path in files:
        try:
            data = probe(path)
        except Exception as exc:
            failures.append(f"无法读取：{path} ({exc})")
            continue
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not NAME_RE.match(path.stem):
            failures.append(f"命名不合规：{path.name}")
        if not video:
            failures.append(f"缺少视频轨：{path}")
            continue
        expected_size = (1920, 1080) if path.stem.endswith(("横", "横包框")) else (1080, 1920)
        if (video.get("width"), video.get("height")) != expected_size:
            failures.append(f"尺寸错误：{path.name}")
        if video.get("r_frame_rate") != "30/1":
            failures.append(f"帧率不是30fps：{path.name}")
        if not audio:
            failures.append(f"缺少音频轨：{path.name}")
    if args.expected is not None and len(files) != args.expected:
        failures.append(f"数量错误：expected={args.expected}, actual={len(files)}")
    print(json.dumps({"count": len(files), "ok": not failures, "failures": failures}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
