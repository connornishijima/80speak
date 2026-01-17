#!/usr/bin/env python3
"""
80speak - DECtalk Text-to-Speech API Server

A FastAPI-based REST API for the DECtalk speech synthesizer.
"""

import os
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
DECTALK_DIR = SCRIPT_DIR / "dectalk"
OUTPUT_DIR = SCRIPT_DIR / "output"
SAY_EXE = DECTALK_DIR / "say.exe"

app = FastAPI(
    title="80speak",
    description="DECtalk Text-to-Speech API - The voice of Stephen Hawking",
    version="1.0.0",
)


class SynthesizeRequest(BaseModel):
    """Request body for text-to-speech synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")


class SynthesizeResponse(BaseModel):
    """Response body for synthesis request."""
    session_id: str
    message: str


@app.on_event("startup")
async def startup():
    """Validate DECtalk is available on startup."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not SAY_EXE.exists():
        raise RuntimeError(f"DECtalk say.exe not found at {SAY_EXE}")

    # Check Wine is available
    result = subprocess.run(["wine", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Wine is not available or not working")

    print(f"80speak API started. DECtalk: {SAY_EXE}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "engine": "dectalk"}


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest):
    """
    Synthesize text to speech using DECtalk.

    Returns a session ID that can be used to download the audio file.
    """
    session_id = str(uuid.uuid4())
    output_file = OUTPUT_DIR / f"{session_id}.wav"

    command = ["wine", str(SAY_EXE), "-w", str(output_file), request.text]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=str(DECTALK_DIR),
        timeout=30,
    )

    if result.returncode != 0 or not output_file.exists():
        raise HTTPException(
            status_code=500,
            detail=f"DECtalk synthesis failed: {result.stderr}"
        )

    return SynthesizeResponse(
        session_id=session_id,
        message="Synthesis complete"
    )


@app.get("/audio/{session_id}")
async def get_audio(session_id: str):
    """
    Download the synthesized audio file.

    The session_id is returned from the /synthesize endpoint.
    """
    # Validate session_id format (UUID)
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    output_file = OUTPUT_DIR / f"{session_id}.wav"

    if not output_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=str(output_file),
        media_type="audio/wav",
        filename=f"{session_id}.wav"
    )


@app.delete("/audio/{session_id}")
async def delete_audio(session_id: str):
    """Delete a synthesized audio file."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    output_file = OUTPUT_DIR / f"{session_id}.wav"

    if output_file.exists():
        output_file.unlink()
        return {"message": "Audio file deleted"}

    raise HTTPException(status_code=404, detail="Audio file not found")
