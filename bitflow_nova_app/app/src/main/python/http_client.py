# http_client.py
# Centralised HTTP client factory for all crawler modules.
# All SSL / timeout / rate-limit configuration lives here.

import httpx
import time
import threading

# ---------------------------------------------------------------------------
# Global configuration – change here to affect every module at once
# ---------------------------------------------------------------------------

# Set False ONLY when scanning sites known to use self-signed / internal CAs.
# Users can override via start_crawl(verify_ssl=False).
VERIFY_SSL: bool = True

# Default per-request timeouts (seconds)
DEFAULT_TIMEOUT: int = 20
PROBE_TIMEOUT: int   = 5   # Shorter for hidden-path / subdomain probes

# Rate limiting: max requests per second across all threads
# 8 req/s is ethical for external sites; raise carefully for internal targets.
MAX_RPS: float = 8.0

# ---------------------------------------------------------------------------
# Simple token-bucket rate limiter
# ---------------------------------------------------------------------------
_rps_lock = threading.Lock()
_rps_last_call: float = 0.0
_rps_tokens: float = MAX_RPS       # start full


def _acquire_token() -> None:
    """Block until a rate-limit token is available."""
    global _rps_last_call, _rps_tokens
    with _rps_lock:
        now = time.monotonic()
        elapsed = now - _rps_last_call
        _rps_last_call = now
        # Refill tokens proportional to elapsed time
        _rps_tokens = min(MAX_RPS, _rps_tokens + elapsed * MAX_RPS)
        if _rps_tokens >= 1.0:
            _rps_tokens -= 1.0
        else:
            sleep_for = (1.0 - _rps_tokens) / MAX_RPS
            time.sleep(sleep_for)
            _rps_tokens = 0.0


# ---------------------------------------------------------------------------
# Public factory function
# ---------------------------------------------------------------------------

def make_client(
    timeout: int = DEFAULT_TIMEOUT,
    follow_redirects: bool = True,
    verify: bool | None = None,      # None → use module-level VERIFY_SSL
    rate_limit: bool = True,
) -> httpx.Client:
    """Return a configured httpx.Client.

    Parameters
    ----------
    timeout:          Request timeout in seconds.
    follow_redirects: Follow HTTP redirects automatically.
    verify:           Override SSL verification setting.
                      Pass False only for self-signed-cert targets.
    rate_limit:       Apply global token-bucket rate limiter before returning
                      the client.  Disable only for fire-and-forget probes
                      that already manage their own concurrency.
    """
    if rate_limit:
        _acquire_token()

    ssl_verify = verify if verify is not None else VERIFY_SSL

    return httpx.Client(
        timeout=timeout,
        follow_redirects=follow_redirects,
        verify=ssl_verify,
        headers={"User-Agent": "CyberRecon/1.0 (+https://bitflow.app)"},
    )


def make_async_client(
    timeout: int = DEFAULT_TIMEOUT,
    follow_redirects: bool = True,
    verify: bool | None = None,
) -> httpx.AsyncClient:
    """Async variant – does NOT apply rate limiting (caller manages it)."""
    ssl_verify = verify if verify is not None else VERIFY_SSL
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        verify=ssl_verify,
    )
