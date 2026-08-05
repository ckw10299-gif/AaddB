import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output_json")
    parser.add_argument("--glossary")
    parser.add_argument("--model", default="large-v3-turbo")
    args = parser.parse_args()

    terms = []
    if args.glossary:
        terms = [
            line.strip()
            for line in Path(args.glossary).read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    hotwords = "，".join(terms)
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    iterator, info = model.transcribe(
        args.input,
        language="zh",
        beam_size=5,
        best_of=5,
        temperature=0,
        vad_filter=False,
        condition_on_previous_text=True,
        word_timestamps=True,
        hotwords=hotwords or None,
        initial_prompt=(
            f"真人游戏广告中文对白。专有名词：{hotwords}。完整转写每一句对白，不要省略短句。"
            if hotwords else "真人游戏广告中文对白。完整转写每一句对白，不要省略短句。"
        ),
    )
    segments = []
    for segment in iterator:
        segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "avg_logprob": segment.avg_logprob,
            "no_speech_prob": segment.no_speech_prob,
            "words": [
                {
                    "start": word.start,
                    "end": word.end,
                    "word": word.word.strip(),
                    "probability": word.probability,
                }
                for word in (segment.words or []) if word.word.strip()
            ],
        })
    Path(args.output_json).write_text(
        json.dumps({"language": info.language, "segments": segments}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
