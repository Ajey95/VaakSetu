from datetime import UTC, datetime, timedelta
from app.tools.cache import ContextCache


def test_cache_ttl_varies_by_data_type_and_preserves_provenance():
    now = datetime(2026, 8, 12, tzinfo=UTC)
    cache = ContextCache(clock=lambda: now)
    market = cache.put("market:manchester", {"value": 3.1}, ["source-1"], topic="market")
    property_item = cache.put("epc:123", {"rating": "C"}, ["source-2"], topic="property")
    assert market.expires_at == now + timedelta(hours=6)
    assert property_item.expires_at == now + timedelta(days=30)
    assert cache.get("market:manchester").source_ids == ["source-1"]


def test_expired_item_is_never_returned_as_fresh():
    current = [datetime(2026, 8, 12, tzinfo=UTC)]
    cache = ContextCache(clock=lambda: current[0])
    cache.put("weather:m1", {"rain": True}, ["met"], topic="weather")
    current[0] += timedelta(hours=2)
    assert cache.get("weather:m1") is None

