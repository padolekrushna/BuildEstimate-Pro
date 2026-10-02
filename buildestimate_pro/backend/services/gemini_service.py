import json
import os
from pathlib import Path
from typing import Any, Dict

import requests


class GeminiService:
    """Minimal Gemini-backed PDF answer service.

    Uses the Google Generative AI REST API with the provided Gemini API key.
    The PDF is extracted to text locally and then sent to Gemini with a prompt.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or "AIzaSyAha_9eiGS_Iq0_uPRQBO9O8y5tsZZin-M"
        self.models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
        self.model = self.models[0]

    def _extract_pdf_text(self, pdf_path: str) -> str:
        import fitz

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(str(path))

        doc = fitz.open(str(path))
        parts = []
        for page in doc:
            text = page.get_text("text")
            if text:
                parts.append(text)
        return "\n\n".join(parts)

    def ask(self, question: str, pdf_path: str) -> Any:
        text = self._extract_pdf_text(pdf_path)
        prompt = (
            "You are a building estimation assistant. Use only the supplied PDF text. "
            "Answer the user's question concisely and cite the exact DSR / section / clause if available. "
            "If the answer is not in the document, say so clearly.\n\n"
            f"Question: {question}\n\nPDF_TEXT:\n{text[:200000]}"
        )

        last_error = None
        for model in self.models:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={self.api_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
            }
            try:
                resp = requests.post(url, json=payload, timeout=120)
                if resp.status_code == 404:
                    last_error = resp.text
                    continue
                resp.raise_for_status()
                data = resp.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    return data
            except requests.RequestException as exc:
                last_error = str(exc)
                continue

        raise RuntimeError(f"No Gemini model worked for this API key. Last error: {last_error}")
