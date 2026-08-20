import argparse
import json
import re
import subprocess
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
TRANSITION = 0.4


def probe(path):
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)]
    return json.loads(subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8").stdout)


def media_info(path):
    data = probe(path)
    video = next(s for s in data["streams"] if s.get("codec_type") == "video")
    return float(data["format"]["duration"]), int(video["width"]), int(video["height"])


def orientation(path):
    _, width, height = media_info(path)
    return "horizontal" if width > height else "vertical"


def find_by_orientation(root, wanted):
    matches = [p for p in Path(root).iterdir() if p.suffix.lower() in VIDEO_EXTENSIONS and orientation(p) == wanted]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {wanted} A video in {root}, found {len(matches)}")
    return matches[0]


def find_b(root, code, wanted):
    matches = [
        p for p in Path(root).rglob("*") if p.suffix.lower() in VIDEO_EXTENSIONS
        and re.search(fr"V{re.escape(code)}-", p.name, re.I) and orientation(p) == wanted
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one V{code} {wanted} B video, found {len(matches)}")
    return matches[0]


def find_endcard(root, category, wanted):
    resolution = "1920x1080" if wanted == "horizontal" else "1080x1920"
    matches = [p for p in Path(root).iterdir() if p.suffix.lower() in VIDEO_EXTENSIONS and category in p.stem and resolution in p.stem]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {category} {wanted} endcard, found {len(matches)}")
    return matches[0]


def b_name(path):
    return path.stem.split(";")[-1].strip()


def render_abc(a, b, c, output, wanted, a_offset, b_cut):
    width, height = (1920, 1080) if wanted == "horizontal" else (1080, 1920)
    a_duration, _, _ = media_info(a)
    source_b_duration, _, _ = media_info(b)
    if b_cut is None:
        raise ValueError(f"Missing verified old-endcard cut for {b.name}")
    b_duration = min(source_b_duration, float(b_cut))
    c_offset = a_offset + b_duration - TRANSITION
    t1_end, t2_end = a_offset + TRANSITION, c_offset + TRANSITION
    delay_b, delay_c = round(a_offset * 1000), round(c_offset * 1000)
    fc = (
        f"[0:v]scale={width}:{height}:flags=lanczos,fps=30,setpts=PTS-STARTPTS[av];"
        f"[1:v]trim=0:{b_duration},scale={width}:{height}:flags=lanczos,fps=30,setpts=PTS-STARTPTS[bv];"
        f"[2:v]scale={width}:{height}:flags=lanczos,fps=30,setpts=PTS-STARTPTS[cv];"
        f"[av][bv]xfade=transition=zoomin:duration={TRANSITION}:offset={a_offset}[ab];"
        f"[ab][cv]xfade=transition=zoomin:duration={TRANSITION}:offset={c_offset}[abc];"
        "[abc]split=5[s0][s1][s2][s3][s4];"
        f"[s0]trim=0:{a_offset},setpts=PTS-STARTPTS[p0];"
        f"[s1]trim={a_offset}:{t1_end},setpts=PTS-STARTPTS[m1];"
        f"[s2]trim={t1_end}:{c_offset},setpts=PTS-STARTPTS[p1];"
        f"[s3]trim={c_offset}:{t2_end},setpts=PTS-STARTPTS[m2];"
        f"[s4]trim=start={t2_end},setpts=PTS-STARTPTS[p2];"
        f"color=c=black:s={width}x{height}:r=30:d={TRANSITION},geq=lum='255*pow(hypot(X-W/2,Y-H/2)/hypot(W/2,H/2),1.7)'[mask1];"
        f"color=c=black:s={width}x{height}:r=30:d={TRANSITION},geq=lum='255*pow(hypot(X-W/2,Y-H/2)/hypot(W/2,H/2),1.7)'[mask2];"
        "[m1][mask1]varblur=min_r=0:max_r=14:planes=15[blur1];"
        "[m2][mask2]varblur=min_r=0:max_r=14:planes=15[blur2];"
        "[p0][blur1][p1][blur2][p2]concat=n=5:v=1:a=0[v];"
        f"[0:a]aresample=48000,atrim=0:{a_duration},asetpts=PTS-STARTPTS[aa];"
        f"[1:a]aresample=48000,atrim=0:{b_duration},asetpts=PTS-STARTPTS,afade=t=in:st=0:d={TRANSITION},"
        f"afade=t=out:st={max(0.0, b_duration-TRANSITION)}:d={TRANSITION},adelay={delay_b}|{delay_b}[ba];"
        f"[2:a]aresample=48000,afade=t=in:st=0:d={TRANSITION},adelay={delay_c}|{delay_c}[ca];"
        "[aa][ba][ca]amix=inputs=3:duration=longest:dropout_transition=0:normalize=0[a]"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(a), "-i", str(b), "-i", str(c), "-filter_complex", fc,
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(output),
    ], check=True)


def frame_version(source, frame, output, target):
    if target == "horizontal":
        canvas, scale, x, y = (1920, 1080), "608:1080", 656, 0
    else:
        canvas, scale, x, y = (1080, 1920), "1080:608", 0, 647
    fc = f"[1:v]scale={scale}:flags=lanczos[content];[0:v][content]overlay={x}:{y}:shortest=1[v]"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(frame), "-i", str(source), "-filter_complex", fc,
        "-map", "[v]", "-map", "1:a?", "-r", "30", "-s", f"{canvas[0]}x{canvas[1]}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy",
        "-movflags", "+faststart", "-shortest", str(output),
    ], check=True)


def main():
    parser = argparse.ArgumentParser(description="Render approved A+B+C pairs and framed counterparts")
    parser.add_argument("a_root")
    parser.add_argument("b_root")
    parser.add_argument("fixed_root")
    parser.add_argument("output_root")
    parser.add_argument("--a-name", required=True)
    parser.add_argument("--codes", nargs="+", required=True)
    parser.add_argument("--a-offset-horizontal", type=float, required=True)
    parser.add_argument("--a-offset-vertical", type=float, required=True)
    parser.add_argument("--b-cut", action="append", default=[], help="Verified old-endcard cut: CODE=seconds or CODE:orientation=seconds")
    args = parser.parse_args()

    cuts = {}
    for item in args.b_cut:
        key, value = item.split("=", 1)
        cuts[key.lower().lstrip("v")] = float(value)
    fixed = Path(args.fixed_root)
    frames = {
        "horizontal": next((fixed / "包框").glob("*1920×1080*.png")),
        "vertical": next((fixed / "包框").glob("*1080×1920*.png")),
    }
    offsets = {"horizontal": args.a_offset_horizontal, "vertical": args.a_offset_vertical}
    names = {"horizontal": "横", "vertical": "竖"}
    outputs = []
    for code in args.codes:
        clean_code = code.lower().lstrip("v")
        for wanted in ("horizontal", "vertical"):
            a = find_by_orientation(args.a_root, wanted)
            b = find_b(args.b_root, clean_code, wanted)
            cut = cuts.get(f"{clean_code}:{wanted}", cuts.get(clean_code))
            other = "vertical" if wanted == "horizontal" else "horizontal"
            for category in ("预约", "体验"):
                c = find_endcard(fixed / "尾板", category, wanted)
                folder = Path(args.output_root) / category
                stem = f"{args.a_name}+V{clean_code}+{b_name(b)}"
                native = folder / f"{stem}+{names[wanted]}.mp4"
                framed = folder / f"{stem}+{names[other]}包框.mp4"
                render_abc(a, b, c, native, wanted, offsets[wanted], cut)
                frame_version(native, frames[other], framed, other)
                outputs.extend([str(native), str(framed)])
    print(json.dumps({"count": len(outputs), "outputs": outputs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
