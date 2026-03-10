---
name: claw-audio
description: Use a self-hosted TTS API server to generate speech from text, upload reference audio, manage speaker presets, and prepare audio for chat voice messages. Use when the user wants local voice generation, reference-audio voice cloning, speaker testing, WAV/Opus generation, or chat voice replies through a custom TTS backend.
---

# claw-audio

Use the user's local TTS server when they want locally hosted voice generation or reference-audio-based speaker workflows.

## Quick start

```bash
python3 claw-audio/scripts/tts_client.py health
python3 claw-audio/scripts/tts_client.py speakers
python3 claw-audio/scripts/tts_client.py tts \
  --speaker Scarlett-60s \
  --text "Hello from the local TTS service" \
  --out /tmp/claw-audio-test.wav
```

Convert to Opus for chat voice messages:

```bash
ffmpeg -y -i /tmp/claw-audio-test.wav -c:a libopus -b:a 32k /tmp/claw-audio-test.opus
```

## Default server

The helper script defaults to a local TTS endpoint:

- `http://192.168.122.165:8002`

Override with `--base-url` when needed.

## Tasks

### Check server health

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

### Generate speech

```bash
python3 claw-audio/scripts/tts_client.py tts \
  --speaker Scarlett-60s \
  --text "Hi Michael. This is an English test." \
  --out /tmp/out.wav
```

Use `--prompt-speech-path` instead of `--speaker` only if the server expects a direct prompt path.

### Prepare a chat voice message

1. Generate WAV with the script.
2. Convert WAV to Opus with ffmpeg.
3. Send the `.opus` file as a voice message.

## Notes

- `/tts` requires either `speaker` or `prompt_speech_path`.
- The server returns WAV audio.
- Convert to Opus before sending to chat surfaces that prefer voice-note playback.
- If requests fail with connection errors, verify the server is running and listening on the configured port.
