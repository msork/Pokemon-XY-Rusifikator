"""Bounded local model inference for artwork review."""
from __future__ import annotations

import base64
from contextlib import contextmanager
from http.client import HTTPConnection
from io import BytesIO
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
from time import monotonic, sleep

from PIL import Image

OCR_PROMPT = (
    "Transcribe the visible English lettering on this video game texture exactly. "
    "Keep spelling and line order. Return only the transcription on one line. "
    "If there is no legible English text, return NONE. Do not infer missing letters."
)
PROMPT_VERSION = 1


class LocalArtworkModel:
    def __init__(self, executable: Path, weights: Path, device: str, projector: Path | None = None):
        self.executable = executable.resolve(strict=True)
        self.weights = weights.resolve(strict=True)
        self.projector = projector.resolve(strict=True) if projector else None
        self.device = device
        self.port = 0
        self.api_key = ""

    def _request(self, endpoint, body=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=90)
        try:
            conn.request("POST" if body else "GET", endpoint, json.dumps(body) if body else None,
                         {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"})
            response = conn.getresponse()
            payload = json.loads(response.read(256 * 1024))
            return response.status, payload
        finally:
            conn.close()

    @contextmanager
    def session(self, log: Path):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            self.port = reservation.getsockname()[1]
        command = [
            str(self.executable), "--model", str(self.weights), "--host", "127.0.0.1",
            "--port", str(self.port), "--parallel", "1", "--ctx-size", "4096", "--no-webui",
            "--threads", "4", "--device", self.device, "--n-gpu-layers", "0" if self.device == "none" else "99",
        ]
        if self.projector:
            command += ["--mmproj", str(self.projector)]
        self.api_key = secrets.token_urlsafe(32)
        env = {**os.environ, "LLAMA_API_KEY": self.api_key}
        with log.open("wb") as output, subprocess.Popen(command, stdout=output, stderr=output, env=env) as process:
            try:
                deadline = monotonic() + 120
                while monotonic() < deadline and process.poll() is None:
                    try:
                        status, _ = self._request("/health")
                        if status == 200:
                            break
                    except (OSError, ValueError):
                        pass
                    sleep(0.2)
                else:
                    raise RuntimeError(f"Local artwork model failed to start. See {log}")
                yield self
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()

    def _complete(self, content, limit):
        status, payload = self._request("/v1/chat/completions", {
            "messages": [{"role": "user", "content": content}],
            "temperature": 0, "top_k": 1, "seed": 17, "max_tokens": limit,
            "chat_template_kwargs": {"enable_thinking": False},
        })
        if status != 200:
            raise RuntimeError(f"Local artwork model request failed ({status})")
        choice = payload["choices"][0]
        text = choice["message"]["content"]
        return text.strip() if choice["finish_reason"] == "stop" and isinstance(text, str) else ""

    def read(self, image: Image.Image) -> str:
        background = Image.new("RGBA", image.size, (92, 92, 92, 255))
        background.alpha_composite(image)
        frame = background.convert("RGB")
        scale = min(4, 768 / max(frame.size))
        frame = frame.resize(tuple(max(1, round(side * scale)) for side in frame.size), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        frame.save(buffer, format="PNG")
        url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
        text = self._complete([{"type": "text", "text": OCR_PROMPT},
                               {"type": "image_url", "image_url": {"url": url}}], 60)
        text = " ".join(text.split())
        if text.upper() == "NONE" or len(text) > 170:
            return ""
        return text

    def translate(self, english: str, context: tuple[str, ...], terms: dict[str, str]) -> str:
        prompt = (
            "Translate the following Pokémon video game interface text from English to Russian. "
            "Use concise, natural Russian and preserve numbers. Return exactly one line of Russian "
            "with no explanation or quotes. Apply the required glossary.\n"
            + json.dumps({"source": english, "context": context, "required_glossary": terms}, ensure_ascii=False)
        )
        text = self._complete(prompt, 80)
        return text if len(text) <= 200 and not re.search(r"[\r\n]", text) else ""
