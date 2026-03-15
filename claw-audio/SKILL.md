---
name: claw-audio
description: Use a self-hosted TTS API server to generate speech from text, upload reference audio, manage speaker presets, and prepare audio for chat voice messages. Use when the user wants local voice generation, reference-audio voice cloning, speaker testing, WAV/Opus generation, or chat voice replies through a custom TTS backend.
---

# claw-audio

Use the user's local IndexTTS / clawaudio-tts server for locally hosted voice generation, speaker management, and chat-ready audio output.

## Quick start

Check the service and list speakers:

```bash
python3 claw-audio/scripts/tts_client.py --base-url http://localhost:8002 health
python3 claw-audio/scripts/tts_client.py --base-url http://localhost:8002 speakers
```

Generate direct Opus output with the basic endpoint:

```bash
python3 claw-audio/scripts/tts_client.py --base-url http://localhost:8002 tts \
  --speaker voice_01 \
  --text "Hello from the local TTS service" \
  --output-format opus \
  --out /tmp/claw-audio-test.opus
```

Generate expressive speech with the enhanced endpoint:

```bash
python3 claw-audio/scripts/tts_client.py --base-url http://localhost:8002 tts-v2 \
  --speaker voice_12 \
  --text "快躲起来，他要来了。" \
  --output-format opus \
  --emo-control-mode 3 \
  --use-emo-text \
  --emo-text 恐惧 \
  --out /tmp/fear.opus
```

## Default server

The helper script currently defaults to:

- `http://localhost:8002`

Override the base URL whenever the deployment differs.

## Output formats

Non-streaming endpoints support:

- `wav`
- `flac`
- `opus`

When `--output-format opus` is used, the API returns Opus audio in an Ogg container (`audio/ogg`). Prefer this for chat voice messages when the chat surface accepts Opus.

## Endpoints and workflows

### Check service health

```bash
python3 claw-audio/scripts/tts_client.py health
```

### List available speakers

```bash
python3 claw-audio/scripts/tts_client.py speakers
```

### Upload a reference audio file

```bash
python3 claw-audio/scripts/tts_client.py upload --file path/to/reference.mp3
```

The upload endpoint accepts `.wav` and `.mp3`.

### Generate speech with `/tts`

Use for straightforward TTS when you do not need emotion controls.

```bash
python3 claw-audio/scripts/tts_client.py tts \
  --speaker voice_01 \
  --text "你好，这是基础接口测试。" \
  --output-format opus \
  --out /tmp/out.opus
```

### Generate speech with `/tts_v2`

Use for richer control, especially emotion-driven delivery.

```bash
python3 claw-audio/scripts/tts_client.py tts-v2 \
  --speaker voice_10 \
  --text "哇，这个效果非常自然。" \
  --output-format flac \
  --emo-control-mode 2 \
  --emo-vector '[0,0,0,0,0,0,0.45,0]' \
  --out /tmp/out.flac
```

Text emotion control example:

```bash
python3 claw-audio/scripts/tts_client.py tts-v2 \
  --speaker voice_12 \
  --text "快躲起来，他要来了。" \
  --output-format opus \
  --emo-control-mode 3 \
  --use-emo-text \
  --emo-text 恐惧 \
  --out /tmp/fear.opus
```

### Stream long-form generation with `/tts_stream`

Use `stream_protocol=audio` only with WAV output:

```bash
python3 claw-audio/scripts/tts_client.py tts-stream \
  --speaker voice_01 \
  --text "这是一段很长的文本，用于测试流式播放能力。" \
  --stream-protocol audio \
  --output-format wav \
  --max-segment-length 60 \
  --out /tmp/stream.wav
```

Use `stream_protocol=ndjson` for programmatic consumption and segmented Opus output:

```bash
python3 claw-audio/scripts/tts_client.py tts-stream \
  --speaker voice_01 \
  --text "这是一段较长的文本，会被分成多个段落进行流式生成。" \
  --stream-protocol ndjson \
  --output-format opus \
  --audio-encoding base64 \
  --events-out /tmp/stream-events.jsonl \
  --out /tmp/stream.opus
```

## Parameter guidance

Pass at least one of:

- `--speaker`
- `--prompt-speech-path`

Useful controls:

- `--strict-speaker-match` to avoid fuzzy speaker matches
- `--output-format opus` for chat-friendly voice delivery
- `--emo-control-mode 1|2|3` for emotion control on `tts-v2` and `tts-stream`
- `--emo-text` with `--use-emo-text` for text-driven emotion
- `--emo-vector` for explicit emotion vectors in the order `[喜, 怒, 哀, 惧, 厌恶, 低落, 惊喜, 平静]`
- `--max-segment-length` for long streaming jobs
- `--events-out` to keep raw NDJSON event logs for debugging or later assembly

## Preparing chat voice messages

Preferred order:

1. Request `--output-format opus` directly from the API.
2. Send the resulting `.opus` / Ogg-Opus file if the chat surface accepts it.
3. Only transcode with ffmpeg when the receiving surface requires a different container or bitrate.

Fallback transcode example:

```bash
ffmpeg -y -i /tmp/input.wav -c:a libopus -b:a 32k /tmp/output.opus
```

## Notes

- `/tts` and `/tts_v2` return binary audio directly.
- `output_format=opus` maps to an `audio/ogg` response.
- `/tts_stream` with `stream_protocol=audio` currently supports only WAV.
- `/tts_stream` with `stream_protocol=ndjson` can emit `wav`, `flac`, or `opus` metadata and base64 audio chunks.
- If requests fail with connection errors, verify the service is running and listening on the configured host and port.
- If a chat workflow unexpectedly sends MP3, treat that as a higher-level toolchain default rather than a limitation of the clawaudio-tts API.
