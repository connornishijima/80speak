# 80speak

A REST API for the DECtalk text-to-speech synthesizer, famously used by Professor Stephen Hawking, the US National Weather Service, Back To The Future Part II, and Benny Benassi.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Wine (for running DECtalk on Linux)
- DECtalk binaries (included in `dectalk/` directory)

## Quick Start

### 1. Install Wine

```bash
# Ubuntu/Debian
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wine32

# macOS (via Homebrew)
brew install --cask wine-stable
```

### 2. Install Dependencies & Run

```bash
# Using uv (recommended)
uv run uvicorn main:app --reload

# Or with pip
pip install -e .
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Health Check

```bash
GET /health
```

Returns API status.

### Synthesize Speech

```bash
POST /synthesize
Content-Type: application/json

{
  "text": "Hello, I am DECtalk."
}
```

Returns:
```json
{
  "session_id": "uuid-here",
  "message": "Synthesis complete"
}
```

### Download Audio

```bash
GET /audio/{session_id}
```

Returns the WAV audio file.

### Delete Audio

```bash
DELETE /audio/{session_id}
```

Removes the audio file from the server.

## Example Usage

```bash
# Synthesize text
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  -o response.json

# Get session_id from response and download audio
curl http://localhost:8000/audio/SESSION_ID -o speech.wav

# Play the audio (Linux)
aplay speech.wav
```

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security Considerations

**This application has significant security risks and should only be run in a sandboxed environment or on a trusted internal network.**

### Risk Assessment

| Risk | Severity | Description |
|------|----------|-------------|
| Command Injection | **HIGH** | User-provided text is passed to Wine/DECtalk subprocess. While we use list-based subprocess calls (not shell=True), DECtalk may interpret special characters. |
| Denial of Service | **MEDIUM** | No rate limiting. Large text inputs or many concurrent requests could exhaust system resources. |
| Disk Exhaustion | **MEDIUM** | Generated audio files accumulate in `output/`. No automatic cleanup mechanism. |
| Wine Attack Surface | **MEDIUM** | Wine adds a large attack surface. DECtalk DLLs are legacy Windows binaries with unknown vulnerabilities. |
| Path Traversal | **LOW** | Session IDs are validated as UUIDs, preventing path traversal in audio retrieval. |

### Recommended Mitigations

1. **Run in a container** (Docker) with resource limits
2. **Add rate limiting** (e.g., slowapi middleware)
3. **Implement audio file cleanup** (cron job or TTL-based deletion)
4. **Network isolation** - bind to localhost only, use reverse proxy with auth
5. **Input sanitization** - filter DECtalk control codes if not desired
6. **Resource limits** - set `timeout` on subprocess calls (already implemented at 30s)

### DECtalk Control Codes

DECtalk accepts special control codes in text that modify speech. Examples:
- `[:rate 200]` - Change speech rate
- `[:pitch 100]` - Change pitch
- `[:phoneme on]` - Enable phoneme mode

These could be used for unexpected behavior but are generally harmless.

## License

GNU General Public License v3 (GPL-3.0)
