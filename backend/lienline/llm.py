"""Model access for this project.

The first configured backend wins, in this order:

1. ``GEMINI_API_KEY``          Google Gemini API (OpenAI-compatible endpoint).
2. ``NEBIUS_API_KEY``          Nebius Token Factory, NVIDIA Nemotron open models.
3. ``LLM_BASE_URL`` + ``LLM_API_KEY`` + ``LLM_MODEL``   any other OpenAI-compatible server.
4. ``AI_GATEWAY_API_KEY``      Vercel AI Gateway.
5. Local Ollama                Gemma 4 (``gemma4:e4b``) on the laptop, no account needed.

Set ``LLM_BACKEND`` to one of ``gemini``, ``nebius``, ``custom``, ``gateway`` or ``ollama`` to force one.

Every backend speaks the OpenAI chat/embeddings API, so the rest of the app never
cares which one is live. No Google Cloud SDK, no Application Default Credentials.

Every call is cached on disk (keyed by backend, model, prompt and image hashes),
and every call is recorded in a per-run trace so the UI can show what the model did.
"""

from __future__ import annotations

import base64
import contextvars
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

CACHE_DIR = Path(os.environ.get("LLM_CACHE_DIR", Path(__file__).resolve().parent.parent / ".cache" / "llm"))

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class Backend:
    name: str
    base_url: str
    api_key: str
    chat_model: str
    vision_model: str
    embed_model: str


def _ollama_up(base: str) -> bool:
    try:
        return httpx.get(base.replace("/v1", "") + "/api/version", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def _gemini() -> Backend:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    return Backend("gemini", "https://generativelanguage.googleapis.com/v1beta/openai", os.environ["GEMINI_API_KEY"],
                   model, os.environ.get("GEMINI_VISION_MODEL", model), os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001"))


def _nebius() -> Backend:
    model = os.environ.get("NEBIUS_MODEL", "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5")
    return Backend("nebius", os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"), os.environ["NEBIUS_API_KEY"],
                   model, os.environ.get("NEBIUS_VISION_MODEL", "nvidia/Nemotron-Nano-VL-12B-V2"),
                   os.environ.get("NEBIUS_EMBED_MODEL", "BAAI/bge-multilingual-gemma2"))


def _custom() -> Backend:
    model = os.environ["LLM_MODEL"]
    return Backend("custom", os.environ["LLM_BASE_URL"].rstrip("/"), os.environ.get("LLM_API_KEY", "none"),
                   model, os.environ.get("LLM_VISION_MODEL", model), os.environ.get("LLM_EMBED_MODEL", model))


def _gateway() -> Backend:
    model = os.environ.get("GATEWAY_MODEL", "google/gemini-3.8-flash")
    return Backend("gateway", "https://ai-gateway.vercel.sh/v1", os.environ["AI_GATEWAY_API_KEY"],
                   model, os.environ.get("GATEWAY_VISION_MODEL", model), os.environ.get("GATEWAY_EMBED_MODEL", "google/gemini-embedding-001"))


def _ollama() -> Backend:
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
    return Backend("ollama", base, "ollama", model, os.environ.get("OLLAMA_VISION_MODEL", model),
                   os.environ.get("OLLAMA_EMBED_MODEL", "embeddinggemma"))


def pick_backend() -> Backend:
    """Return the configured backend. Raise if none is available."""
    forced = os.environ.get("LLM_BACKEND", "").lower()
    makers = {"gemini": _gemini, "nebius": _nebius, "custom": _custom, "gateway": _gateway, "ollama": _ollama}
    if forced:
        return makers[forced]()
    if os.environ.get("GEMINI_API_KEY"):
        return _gemini()
    if os.environ.get("NEBIUS_API_KEY"):
        return _nebius()
    if os.environ.get("LLM_BASE_URL") and os.environ.get("LLM_MODEL"):
        return _custom()
    if os.environ.get("AI_GATEWAY_API_KEY"):
        return _gateway()
    b = _ollama()
    if _ollama_up(b.base_url):
        return b
    raise RuntimeError(
        "No model backend available. Set GEMINI_API_KEY, NEBIUS_API_KEY, or LLM_BASE_URL/LLM_MODEL, "
        "or start Ollama (`brew services start ollama`, `ollama pull gemma4:e4b`)."
    )


def describe_backend() -> dict[str, str]:
    """Small dict for the UI's 'model' badge."""
    try:
        b = pick_backend()
        return {"backend": b.name, "chat_model": b.chat_model, "vision_model": b.vision_model}
    except RuntimeError as e:
        return {"backend": "none", "error": str(e)}


# ---------------------------------------------------------------- trace

@dataclass
class Trace:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def add(self, **kw: Any) -> None:
        self.calls.append(kw)

    def summary(self) -> dict[str, Any]:
        return {
            "calls": len(self.calls),
            "live_calls": sum(1 for c in self.calls if not c.get("cached")),
            "seconds": round(sum(c.get("seconds", 0) for c in self.calls), 1),
            "model_seconds": round(sum(c.get("orig_seconds", 0) for c in self.calls), 1),
            "steps": [c.get("step") for c in self.calls],
        }


_trace: contextvars.ContextVar[Trace | None] = contextvars.ContextVar("llm_trace", default=None)


def start_trace() -> Trace:
    t = Trace()
    _trace.set(t)
    return t


def _record(**kw: Any) -> None:
    t = _trace.get()
    if t is not None:
        t.add(**kw)


# ---------------------------------------------------------------- caching

def _cache_path(kind: str, payload: dict[str, Any]) -> Path:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return CACHE_DIR / kind / digest[:2] / f"{digest}.json"


def _cache_get(path: Path) -> Any | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
    return None


def _cache_put(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value))
    tmp.replace(path)


# ---------------------------------------------------------------- requests

def _post(b: Backend, route: str, body: dict[str, Any], timeout: float = 600) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            r = httpx.post(
                f"{b.base_url}/{route}",
                headers={"Authorization": f"Bearer {b.api_key}", "content-type": "application/json"},
                json=body,
                timeout=timeout,
            )
            if r.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(f"{r.status_code}: {r.text[:200]}", request=r.request, response=r)
            if r.status_code >= 400:
                raise RuntimeError(f"{b.name} {route} failed ({r.status_code}): {r.text[:300]}")
            return r.json()
        except (httpx.HTTPError, httpx.HTTPStatusError) as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{b.name} {route} failed after retries: {last}")


def _image_part(image: bytes | str, mime: str = "image/jpeg") -> dict[str, Any]:
    if isinstance(image, str) and image.startswith(("http://", "https://", "data:")):
        url = image
    else:
        raw = image if isinstance(image, bytes) else Path(image).read_bytes()
        url = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
    return {"type": "image_url", "image_url": {"url": url}}


def _hash_image(image: bytes | str) -> str:
    if isinstance(image, str) and image.startswith(("http://", "https://")):
        return image
    raw = image if isinstance(image, bytes) else Path(image).read_bytes()
    return hashlib.sha256(raw).hexdigest()


def extract_json(text: str) -> Any:
    """Parse JSON from a model reply, tolerating code fences and stray prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start, end = text.find(open_c), text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Model did not return JSON: {text[:200]}")


def chat(
    prompt: str,
    *,
    step: str = "chat",
    system: str | None = None,
    images: list[bytes | str] | None = None,
    image_mime: str = "image/jpeg",
    json_mode: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    use_cache: bool = True,
) -> dict[str, Any]:
    """One chat call. Returns {'text', 'json' (if json_mode), 'backend', 'model', 'cached', 'seconds'}."""
    b = pick_backend()
    model = b.vision_model if images else b.chat_model
    key = {
        "backend": b.name, "model": model, "system": system, "prompt": prompt, "json": json_mode,
        "temperature": temperature, "images": [_hash_image(i) for i in (images or [])],
    }
    path = _cache_path("chat", key)
    if use_cache and (hit := _cache_get(path)) is not None:
        hit["cached"] = True
        _record(step=step, model=model, backend=b.name, cached=True, seconds=0, orig_seconds=hit.get("seconds", 0))
        return hit

    content: list[dict[str, Any]] | str
    if images:
        content = [{"type": "text", "text": prompt}] + [_image_part(i, image_mime) for i in images]
    else:
        content = prompt
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]
    body: dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if b.name == "ollama":
        body["reasoning_effort"] = "none"  # Gemma 4 thinks by default on Ollama; off is much faster for short JSON.
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    t0 = time.time()
    data = _post(b, "chat/completions", body)
    text = data["choices"][0]["message"].get("content") or ""
    if json_mode and data["choices"][0].get("finish_reason") == "length":
        # The reply was cut off mid-JSON: ask once more with twice the room.
        body["max_tokens"] = max_tokens * 2
        data = _post(b, "chat/completions", body)
        text = data["choices"][0]["message"].get("content") or ""
    tokens = int((data.get("usage") or {}).get("total_tokens") or 0)  # LienLine: report token use per run
    out: dict[str, Any] = {"text": text, "backend": b.name, "model": model, "seconds": round(time.time() - t0, 2),
                           "tokens": tokens}
    if json_mode:
        try:
            out["json"] = extract_json(text)
        except ValueError:
            repair = _post(b, "chat/completions", {
                "model": b.chat_model, "temperature": 0, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": "Return only valid JSON for this content, nothing else:\n" + text}],
                "response_format": {"type": "json_object"},
            })
            out["json"] = extract_json(repair["choices"][0]["message"].get("content") or "")
    _cache_put(path, out)
    _record(step=step, model=model, backend=b.name, cached=False, seconds=out["seconds"])
    out["cached"] = False
    return out


def chat_json(prompt: str, **kw: Any) -> Any:
    """Convenience wrapper returning only the parsed JSON."""
    return chat(prompt, json_mode=True, **kw)["json"]


def _unwrap(raw: Any, schema: type[BaseModel]) -> Any:
    """Models sometimes wrap the object in one extra key ({"Scene": {...}}) or return a one-item list."""
    fields = set(schema.model_fields)
    if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], dict):
        raw = raw[0]
    if isinstance(raw, dict) and len(raw) == 1 and not (set(raw) & fields):
        inner = next(iter(raw.values()))
        if isinstance(inner, dict) and set(inner) & fields:
            return inner
    return raw


def chat_model(prompt: str, schema: type[T], **kw: Any) -> T:
    """Ask for JSON matching a Pydantic model. One corrective retry if validation fails."""
    shape = json.dumps(schema.model_json_schema())
    full = f"{prompt}\n\nReturn one JSON object matching this JSON Schema exactly:\n{shape}"
    raw = _unwrap(chat_json(full, **kw), schema)
    try:
        return schema.model_validate(raw)
    except ValidationError as e:
        kw2 = {**kw, "use_cache": False}
        fixed = chat_json(f"{full}\n\nYour previous answer failed validation:\n{e}\nPrevious answer:\n{json.dumps(raw)[:3000]}\nReturn corrected JSON only.", **kw2)
        return schema.model_validate(_unwrap(fixed, schema))


def embed(texts: list[str], *, use_cache: bool = True) -> list[list[float]]:
    """Embed a list of texts. Cached per text."""
    b = pick_backend()
    vectors: list[list[float] | None] = [None] * len(texts)
    todo: list[int] = []
    for i, t in enumerate(texts):
        p = _cache_path("embed", {"backend": b.name, "model": b.embed_model, "text": t})
        if use_cache and (hit := _cache_get(p)) is not None:
            vectors[i] = hit
        else:
            todo.append(i)
    for start in range(0, len(todo), 64):
        batch = todo[start : start + 64]
        data = _post(b, "embeddings", {"model": b.embed_model, "input": [texts[i] for i in batch]})
        for i, item in zip(batch, sorted(data["data"], key=lambda d: d["index"])):
            vectors[i] = item["embedding"]
            _cache_put(_cache_path("embed", {"backend": b.name, "model": b.embed_model, "text": texts[i]}), item["embedding"])
    return [v for v in vectors if v is not None]
