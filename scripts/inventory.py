import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}


def probe(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-show_entries", "stream=codec_type,width,height,r_frame_rate",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True, encoding="utf-8")
    data = json.loads(result.stdout)
    video = next(stream for stream in data["streams"] if stream["codec_type"] == "video")
    audio = next((stream for stream in data["streams"] if stream["codec_type"] == "audio"), None)
    return {
        "width": video["width"], "height": video["height"],
        "fps": video["r_frame_rate"], "duration": float(data["format"]["duration"]),
        "has_audio": audio is not None,
    }


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def orientation(meta):
    if meta["width"] > meta["height"]:
        return "horizontal"
    if meta["height"] > meta["width"]:
        return "vertical"
    return "ambiguous"


def parse_b(path):
    stem = path.stem.strip()
    sequence = re.search(r"(?:^|-)V(\d+)(?:-|$)", stem, re.I)
    requester = re.search(r"-\d{8}-([^-]+)-", stem)
    name = stem.split(";")[-1].strip()
    name = re.sub(r"\s*-\s*??$", "", name).strip()
    return {
        "sequence": f"V{sequence.group(1)}" if sequence else None,
        "requester": requester.group(1) if requester else None,
        "name": name,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--a-requester")
    args = parser.parse_args()
    root = Path(args.root)
    records = []
    seen_b = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTS or "??" in path.parts:
            continue
        meta = probe(path)
        role = "A" if "A?" in path.parts else "B" if "B?" in path.parts else "unknown"
        category = "??" if "??" in path.parts else "??" if "??" in path.parts else None
        item = {"path": str(path), "role": role, "category": category, **meta}
        item["orientation"] = orientation(meta)
        if role == "B":
            item.update(parse_b(path))
            item["sha256"] = sha256(path)
            item["duplicate_of"] = seen_b.get(item["sha256"])
            seen_b.setdefault(item["sha256"], str(path))
        records.append(item)

    unique_b = [record for record in records if record["role"] == "B" and not record.get("duplicate_of")]
    a_files = [record for record in records if record["role"] == "A"]
    counts = {}
    for category in ("??", "??"):
        counts[category] = sum(
            1 for a in a_files for b in unique_b
            if b["category"] == category and a["orientation"] == b["orientation"]
        )
    print(json.dumps({"a_requester": args.a_requester, "counts": counts, "files": records}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
