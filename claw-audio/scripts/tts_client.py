#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE_URL = os.environ.get("CLAW_AUDIO_BASE_URL", "http://localhost:8002")


def http_json(url: str, data: dict | None = None, timeout: int = 120):
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        ctype = resp.headers.get("Content-Type", "")
        if "application/json" in ctype or raw.startswith((b"{", b"[")):
            return json.loads(raw.decode("utf-8", "ignore"))
        return raw


def build_common_payload(args):
    payload = {"text": args.text}
    if getattr(args, "speaker", None):
        payload["speaker"] = args.speaker
    if getattr(args, "prompt_speech_path", None):
        payload["prompt_speech_path"] = args.prompt_speech_path
    if not payload.get("speaker") and not payload.get("prompt_speech_path"):
        raise SystemExit("Pass --speaker or --prompt-speech-path")

    optional_fields = [
        "output_format",
        "strict_speaker_match",
        "temperature",
        "top_k",
        "top_p",
        "seed",
        "max_mel_tokens",
        "num_beams",
        "length_penalty",
        "repetition_penalty",
        "emo_control_mode",
        "emo_audio_prompt",
        "emo_alpha",
        "use_emo_text",
        "emo_text",
        "use_random",
        "interval_silence",
        "do_sample",
    ]
    for field in optional_fields:
        value = getattr(args, field, None)
        if value is not None:
            payload[field] = value

    if getattr(args, "max_text_tokens_per_sentence", None) is not None:
        payload["max_text_tokens_per_sentence"] = args.max_text_tokens_per_sentence
    if getattr(args, "max_text_tokens_per_segment", None) is not None:
        payload["max_text_tokens_per_segment"] = args.max_text_tokens_per_segment
    if getattr(args, "emo_vector", None):
        payload["emo_vector"] = json.loads(args.emo_vector)

    return payload


def save_audio_or_fail(audio, out_path):
    if isinstance(audio, (dict, list)):
        raise SystemExit(f"Unexpected JSON response: {audio}")
    with open(out_path, "wb") as f:
        f.write(audio)
    print(out_path)


def cmd_health(args):
    data = http_json(f"{args.base_url}/", timeout=args.timeout)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_speakers(args):
    data = http_json(f"{args.base_url}/speakers", timeout=args.timeout)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_gpu_status(args):
    data = http_json(f"{args.base_url}/gpu_status", timeout=args.timeout)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_clear_cache(args):
    data = http_json(f"{args.base_url}/clear_cache", data={}, timeout=args.timeout)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_upload(args):
    path = args.file
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    boundary = "----OpenClawBoundary" + uuid.uuid4().hex
    with open(path, "rb") as f:
        file_bytes = f.read()
    body = (
        f"--{boundary}\r\n".encode()
        + f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        + f"Content-Type: {content_type}\r\n\r\n".encode()
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        f"{args.base_url}/upload_audio",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=args.timeout) as resp:
        print(resp.read().decode("utf-8", "ignore"))


def cmd_tts(args):
    payload = build_common_payload(args)
    audio = http_json(f"{args.base_url}/tts", data=payload, timeout=args.timeout)
    save_audio_or_fail(audio, args.out)


def cmd_tts_v2(args):
    payload = build_common_payload(args)
    audio = http_json(f"{args.base_url}/tts_v2", data=payload, timeout=args.timeout)
    save_audio_or_fail(audio, args.out)


def cmd_tts_stream(args):
    payload = build_common_payload(args)
    payload["stream_protocol"] = args.stream_protocol
    payload["include_audio"] = args.include_audio
    payload["audio_encoding"] = args.audio_encoding
    if args.max_segment_length is not None:
        payload["max_segment_length"] = args.max_segment_length

    if args.stream_protocol == "audio":
        if payload.get("output_format") and payload["output_format"] != "wav":
            raise SystemExit("stream_protocol=audio currently expects --output-format wav")
        req = urllib.request.Request(
            f"{args.base_url}/tts_stream",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read()
        save_audio_or_fail(raw, args.out)
        return

    req = urllib.request.Request(
        f"{args.base_url}/tts_stream",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    chunks = []
    events = []
    with urllib.request.urlopen(req, timeout=args.timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "ignore").strip()
            if not line:
                continue
            obj = json.loads(line)
            events.append(obj)
            if obj.get("audio_base64"):
                chunks.append(base64.b64decode(obj["audio_base64"]))

    if args.events_out:
        with open(args.events_out, "w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    if args.include_audio:
        if not chunks:
            raise SystemExit("No audio chunks found in NDJSON stream")
        with open(args.out, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
        print(args.out)
    else:
        print(json.dumps({"events": len(events), "events_out": args.events_out}, ensure_ascii=False))



def add_common_tts_args(sp, *, segment_mode=False):
    sp.add_argument("--speaker")
    sp.add_argument("--prompt-speech-path")
    sp.add_argument("--text", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--output-format", choices=["wav", "flac", "opus"], default="wav")
    sp.add_argument("--strict-speaker-match", action="store_true")
    sp.add_argument("--temperature", type=float)
    sp.add_argument("--top-k", type=int)
    sp.add_argument("--top-p", type=float)
    sp.add_argument("--seed", type=int)
    sp.add_argument("--max-mel-tokens", type=int)
    sp.add_argument("--num-beams", type=int)
    sp.add_argument("--length-penalty", type=float)
    sp.add_argument("--repetition-penalty", type=float)
    if segment_mode:
        sp.add_argument("--max-text-tokens-per-segment", type=int)
    else:
        sp.add_argument("--max-text-tokens-per-sentence", type=int)
    sp.add_argument("--do-sample", action="store_true")
    sp.add_argument("--emo-control-mode", type=int, choices=[0, 1, 2, 3])
    sp.add_argument("--emo-audio-prompt")
    sp.add_argument("--emo-alpha", type=float)
    sp.add_argument("--emo-vector", help='JSON array like "[0,0,0,0,0,0,0.45,0]"')
    sp.add_argument("--use-emo-text", action="store_true")
    sp.add_argument("--emo-text")
    sp.add_argument("--use-random", action="store_true")
    sp.add_argument("--interval-silence", type=float)


def build_parser():
    p = argparse.ArgumentParser(description="clawaudio-tts helper")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=int, default=120)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("health")
    sp.set_defaults(func=cmd_health)

    sp = sub.add_parser("speakers")
    sp.set_defaults(func=cmd_speakers)

    sp = sub.add_parser("gpu-status")
    sp.set_defaults(func=cmd_gpu_status)

    sp = sub.add_parser("clear-cache")
    sp.set_defaults(func=cmd_clear_cache)

    sp = sub.add_parser("upload")
    sp.add_argument("--file", required=True)
    sp.set_defaults(func=cmd_upload)

    sp = sub.add_parser("tts")
    add_common_tts_args(sp, segment_mode=False)
    sp.set_defaults(func=cmd_tts)

    sp = sub.add_parser("tts-v2")
    add_common_tts_args(sp, segment_mode=True)
    sp.set_defaults(func=cmd_tts_v2)

    sp = sub.add_parser("tts-stream")
    add_common_tts_args(sp, segment_mode=True)
    sp.add_argument("--stream-protocol", choices=["audio", "ndjson"], default="ndjson")
    sp.add_argument("--include-audio", action=argparse.BooleanOptionalAction, default=True)
    sp.add_argument("--audio-encoding", choices=["base64", "none"], default="base64")
    sp.add_argument("--max-segment-length", type=int)
    sp.add_argument("--events-out", help="Optional path to save raw NDJSON events as JSONL")
    sp.set_defaults(func=cmd_tts_stream)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(body or str(e), file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
