from unittest.mock import Mock, patch

from controller.sentry.utils import invalidate_cache, is_panic_activated


@patch("controller.sentry.utils.cache")
def test_is_panic_activated(cache: Mock):
    cache.get.return_value = True
    res = is_panic_activated(None)
    assert res["PANIC"]

    cache.get.return_value = False
    res = is_panic_activated(None)
    assert not res["PANIC"]


@patch("controller.sentry.utils.cache")
@patch("controller.sentry.utils.get_cache_key")
def test_invalidate_cache_not_in_cache(get_cache_key: Mock, cache: Mock):
    get_cache_key.return_value = True
    res = invalidate_cache("/sentry/apps/test/")
    assert res == (False, "cache_key does not exist in cache")


@patch("controller.sentry.utils.cache")
@patch("controller.sentry.utils.get_cache_key")
def test_invalidate_cache_key_in_cache(get_cache_key: Mock, cache: Mock):
    get_cache_key.return_value = object()
    cache.__contains__.return_value = True
    res = invalidate_cache("/sentry/apps/test/")
    assert res == (True, "successfully invalidated")
    cache.delete.assert_called_once_with(get_cache_key.return_value)


@patch("controller.sentry.utils.cache")
@patch("controller.sentry.utils.get_cache_key")
def test_invalidate_cache_invalid_key(get_cache_key: Mock, cache: Mock):
    get_cache_key.return_value = None
    res = invalidate_cache("/sentry/apps/test/")
    assert not res[0]
    assert res[1].args[0] == "failed to create cache_key"
