"""Verify the selected device and render a real, non-silent WAV."""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from voxcpm import VoxCPM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    available = torch.cuda.is_available()
    if args.device == "cuda" and not available:
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
    device = ("cuda" if available else "cpu") if args.device == "auto" else args.device
    print(f"torch={torch.__version__} cuda={torch.version.cuda} device={device}", flush=True)
    engine = VoxCPM.from_pretrained(
        args.model, device=device, optimize=False, load_denoiser=False
    )
    wav = np.asarray(engine.generate(
        text="大家好，这是本地配音测试。", cfg_value=2.0, inference_timesteps=10
    ))
    sr = int(engine.tts_model.sample_rate)
    if (
        not np.isfinite(wav).all()
        or not sr // 2 <= len(wav) <= sr * 20
        or float(np.max(np.abs(wav))) < 0.005
    ):
        raise RuntimeError("WAV is invalid, out of expected duration, or effectively silent.")
    sf.write(args.output, wav, sr)
    saved, saved_sr = sf.read(args.output)
    assert saved_sr == sr and len(saved) == len(wav)
    print(f"VERIFIED {args.output} samples={len(saved)} sample_rate={sr}", flush=True)


if __name__ == "__main__":
    main()
