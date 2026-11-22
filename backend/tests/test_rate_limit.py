from app.core.rate_limit import RateLimiter


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("client-a", now=10)
    assert limiter.allow("client-a", now=11)
    assert limiter.allow("client-a", now=12) is False
    assert limiter.allow("client-b", now=12) is True


def test_rate_limiter_expires_old_events():
    limiter = RateLimiter(limit=1, window_seconds=10)
    assert limiter.allow("client-a", now=0)
    assert limiter.allow("client-a", now=5) is False
    assert limiter.allow("client-a", now=11) is True
