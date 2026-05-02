"""
Ollama Client — Phase E
Streams answers from a locally running Ollama instance.
Ollama must be installed and running: https://ollama.com
Recommended models: llama3.2, mistral, phi3
"""
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

OLLAMA_BASE   = 'http://127.0.0.1:11434'
DEFAULT_MODEL = 'llama3.2'

# How many chars of each excerpt to send to the LLM (keeps prompt manageable)
MAX_EXCERPT_CHARS = 600
# Max total context chars sent to Ollama
MAX_CONTEXT_CHARS = 6000


def check_ollama() -> dict:
    """
    Check whether Ollama is running and which models are available.
    Returns: { running: bool, models: [str], default_available: bool }
    """
    try:
        req = urllib.request.Request(f'{OLLAMA_BASE}/api/tags', method='GET')
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        models = [m['name'] for m in data.get('models', [])]
        return {
            'running':           True,
            'models':            models,
            'default_available': any(DEFAULT_MODEL in m for m in models),
        }
    except Exception:
        return {'running': False, 'models': [], 'default_available': False}


def build_prompt(question: str, sources: list[dict]) -> str:
    """
    Build a RAG prompt from the question and retrieved source excerpts.
    Each source contributes up to MAX_EXCERPT_CHARS per excerpt, up to 3 excerpts.
    """
    context_parts = []
    total = 0

    for i, src in enumerate(sources, 1):
        fname = src.get('filename', 'Unknown')
        for excerpt in (src.get('excerpts') or [])[:3]:
            if not excerpt or not excerpt.strip():
                continue
            chunk = excerpt.strip()[:MAX_EXCERPT_CHARS]
            part  = f'[Source {i}: {fname}]\n{chunk}'
            if total + len(part) > MAX_CONTEXT_CHARS:
                break
            context_parts.append(part)
            total += len(part)
        if total >= MAX_CONTEXT_CHARS:
            break

    context = '\n\n'.join(context_parts)

    return f"""You are a helpful assistant that answers questions based ONLY on the provided document excerpts.
If the answer is not in the excerpts, say "I couldn't find that in your documents."
Always mention which source (filename) the information comes from.

DOCUMENT EXCERPTS:
{context}

QUESTION: {question}

ANSWER:"""


def stream_answer(question: str, sources: list[dict], model: str = None):
    """
    Generator that yields text tokens streamed from Ollama.
    Usage:
        for token in stream_answer(question, sources):
            yield token   # or send as SSE
    Yields:
        str tokens as they arrive, or raises OllamaError on failure.
    """
    model   = model or DEFAULT_MODEL
    prompt  = build_prompt(question, sources)
    payload = json.dumps({
        'model':  model,
        'prompt': prompt,
        'stream': True,
        'options': {
            'temperature': 0.2,   # factual, low creativity
            'num_predict': 512,   # max output tokens
        },
    }).encode('utf-8')

    req = urllib.request.Request(
        f'{OLLAMA_BASE}/api/generate',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = obj.get('response', '')
                if token:
                    yield token
                if obj.get('done'):
                    break
    except urllib.error.URLError as e:
        raise OllamaError(f'Cannot reach Ollama at {OLLAMA_BASE}: {e}') from e
    except Exception as e:
        raise OllamaError(str(e)) from e


class OllamaError(Exception):
    pass
