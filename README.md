# clawaudio-skill

A custom TTS skill for OpenClaw voice message workflows.

This repository contains a skill that uses a self-hosted TTS API server to:

- check server health
- list available speakers
- upload reference audio
- generate speech from text
- prepare audio for chat voice messages

## Repository layout

- `.agents/skills/index-tts/SKILL.md` — skill instructions
- `.agents/skills/index-tts/scripts/index_tts.py` — helper CLI for the local TTS server
- `index-tts.skill` — packaged skill artifact

## Default server

The helper script currently defaults to a local TTS endpoint:

- `http://192.168.122.165:8002`

You can override it with `--base-url` or the `INDEX_TTS_BASE_URL` environment variable.

## Quick start

Check the server:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py health
```

List speakers:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py speakers
```

Upload a reference audio file:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py upload --file path/to/reference.mp3
```

Generate WAV from text:

```bash
python3 .agents/skills/index-tts/scripts/index_tts.py tts \
  --speaker Scarlett-60s \
  --text "Hello from the local TTS service" \
  --out /tmp/index-tts-test.wav
```

Convert to Opus for chat voice messages:

```bash
ffmpeg -y -i /tmp/index-tts-test.wav -c:a libopus -b:a 32k /tmp/index-tts-test.opus
```

## Notes

- The server returns WAV audio.
- For Feishu voice replies, convert to Opus before sending.
- The skill was built around a local OpenClaw workflow that generates audio and then sends it as a voice message.
