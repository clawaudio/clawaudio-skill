#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE_URL = os.environ.get("INDEX_TTS_BASE_URL", "http://192.168.122.165:8002")


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


def cmd_health(args):
    data = http_json(f"{args.base_url}/", timeout=args.timeout)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_speakers(args):
    data = http_json(f"{args.base_url}/speakers", timeout=args.timeout)
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
    payload = {"text": args.text}
    if args.speaker:
        payload["speaker"] = args.speaker
    if args.prompt_speech_path:
        payload["prompt_speech_path"] = args.prompt_speech_path
    if not payload.get("speaker") and not payload.get("prompt_speech_path"):
        raise SystemExit("Pass --speaker or --prompt-speech-path")
    audio = http_json(f"{args.base_url}/tts", data=payload, timeout=args.timeout)
    if isinstance(audio, (dict, list)):
        raise SystemExit(f"Unexpected JSON response: {audio}")
    with open(args.out, "wb") as f:
        f.write(audio)
    print(args.out)


def build_parser():
    p = argparse.ArgumentParser(description="IndexTTS helper")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=int, default=120)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("health")
    sp.set_defaults(func=cmd_health)

    sp = sub.add_parser("speakers")
    sp.set_defaults(func=cmd_speakers)

    sp = sub.add_parser("upload")
    sp.add_argument("--file", required=True)
    sp.set_defaults(func=cmd_upload)

    sp = sub.add_parser("tts")
    sp.add_argument("--speaker")
    sp.add_argument("--prompt-speech-path")
    sp.add_argument("--text", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_tts)

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
