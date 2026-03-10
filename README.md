# clawaudio-skill

A custom TTS skill for OpenClaw voice message workflows.

## Repository contents

- `claw-audio/SKILL.md` — skill instructions
- `claw-audio/scripts/tts_client.py` — helper CLI for a local TTS server
- `claw-audio.skill` — packaged skill artifact

## What it does

This skill helps an OpenClaw agent:

- check a local TTS service
- list available speakers
- upload reference audio
- generate WAV audio from text
- convert generated audio into a chat-friendly voice message workflow

## Quick start

```bash
python3 claw-audio/scripts/tts_client.py health
python3 claw-audio/scripts/tts_client.py speakers
python3 claw-audio/scripts/tts_client.py tts \
  --speaker Scarlett-60s \
  --text "Hello from the local TTS service" \
  --out /tmp/claw-audio-test.wav
```

Convert to Opus:

```bash
ffmpeg -y -i /tmp/claw-audio-test.wav -c:a libopus -b:a 32k /tmp/claw-audio-test.opus
```
