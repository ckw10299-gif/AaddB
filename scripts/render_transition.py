import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("a")
    parser.add_argument("b")
    parser.add_argument("ass")
    parser.add_argument("output")
    parser.add_argument("--orientation", choices=("vertical", "horizontal"), required=True)
    parser.add_argument("--a-duration", type=float, required=True)
    parser.add_argument("--transition-offset", type=float, required=True)
    parser.add_argument("--transition-duration", type=float, default=0.4)
    args = parser.parse_args()

    width, height = (1080, 1920) if args.orientation == "vertical" else (1920, 1080)
    end = args.transition_offset + args.transition_duration
    delay = round(args.transition_offset * 1000)
    ass = Path(args.ass).resolve().as_posix().replace(":", r"\:")
    fc = (
        f"[0:v]scale={width}:{height}:flags=lanczos,fps=30,ass='{ass}'[av];"
        f"[1:v]scale={width}:{height}:flags=lanczos,fps=30[bv];"
        f"[av][bv]xfade=transition=zoomin:duration={args.transition_duration}:offset={args.transition_offset}[xf];"
        f"[xf]split=3[p0][p1][p2];"
        f"[p0]trim=start=0:end={args.transition_offset},setpts=PTS-STARTPTS[pre];"
        f"[p1]trim=start={args.transition_offset}:end={end},setpts=PTS-STARTPTS[mid];"
        f"[p2]trim=start={end},setpts=PTS-STARTPTS[post];"
        f"color=c=black:s={width}x{height}:r=30:d={args.transition_duration},"
        "geq=lum='255*pow(hypot(X-W/2,Y-H/2)/hypot(W/2,H/2),1.7)'[mask];"
        "[mid][mask]varblur=min_r=0:max_r=14:planes=15[blur];"
        "[pre][blur][post]concat=n=3:v=1:a=0[v];"
        f"[0:a]aresample=48000,atrim=0:{args.a_duration},asetpts=PTS-STARTPTS[aa];"
        f"[1:a]aresample=48000,afade=t=in:st=0:d={args.transition_duration},adelay={delay}|{delay}[ba];"
        "[aa][ba]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a]"
    )
    command = [
        "ffmpeg", "-y", "-i", args.a, "-i", args.b,
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", args.output,
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
