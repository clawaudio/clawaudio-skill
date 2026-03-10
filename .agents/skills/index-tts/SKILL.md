---
name: index-tts
description: Use a self-hosted IndexTTS API server to generate speech from text, upload reference audio, manage speaker presets, and prepare audio for chat voice messages. Use when the user mentions IndexTTS, a local TTS server, speaker cloning/reference audio, testing voices, generating WAV/Opus from text, or sending voice replies through a custom TTS backend.
---

# index-tts

Use the user's IndexTTS server instead of an external TTS provider when they want cloned/reference voices or locally hosted generation.

## Quick start

Use the helper script:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py health
python3 .agents/skills/index-tts/scripts/index_tts.py speakers
python3 .agents/skills/index-tts/scripts/index_tts.py tts \
  --speaker Scarlett-60s \
  --text "Hello from IndexTTS" \
  --out /tmp/index-tts-test.wav
```

Convert to Opus for chat voice messages:

```bash
ffmpeg -y -i /tmp/index-tts-test.wav -c:a libopus -b:a 32k /tmp/index-tts-test.opus
```

## Current default server

Default base URL in the script is:

- `http://192.168.122.165:8002`

Override with `--base-url` when needed.

## Tasks

### Check server health

Run:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py health
```

This calls `/` and verifies the server is reachable.

### List available speakers

Run:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py speakers
```

This calls `/speakers` and prints all known speaker names.

### Upload a reference audio file

Run:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py upload \
  --file path/to/reference.mp3
```

The server returns the stored speaker name. Reuse that speaker name for future generation.

### Generate speech

Run:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py tts \
  --speaker Scarlett-60s \
  --text "Hi Michael. This is an English test." \
  --out /tmp/out.wav
```

Use `--prompt-speech-path` instead of `--speaker` only if the server expects a direct prompt path.

### Prepare a chat voice message

Recommended flow:

1. Generate WAV with the script.
2. Convert WAV to Opus with ffmpeg.
3. Send the `.opus` file with the message tool using `asVoice=true`.

## Current working speaker library

Known uploaded speakers on the user's server include:

- `Dinesen-60s`
- `Churcher-60s`
- `Scarlett-60s`
- `Joa-60s`

Prefer these names exactly as returned by `/speakers`.

## Notes

- `/tts` requires either `speaker` or `prompt_speech_path`.
- The server currently returns WAV audio.
- For Feishu voice replies, convert to Opus before sending.
- If requests fail with connection errors, verify the server is running and listening on port `8002`.
