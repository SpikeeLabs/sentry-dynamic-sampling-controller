from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key


def invalidate_cache(path=""):
    """this function uses Django's caching function get_cache_key(). Since 1.7,
    Django has used more variables from the request object (scheme, host,
    path, and query string) in order to create the MD5 hashed part of the
    cache_key. Additionally, Django will use your server's timezone and
    language as properties as well. If internationalization is important to
    your application, you will most likely need to adapt this function to
    handle that appropriately.
    """

    # Bootstrap request:
    # request.path should point to the view endpoint you want to invalidate
    # request.META must include the correct
    # SERVER_NAME and SERVER_PORT as django uses these in order
    # to build a MD5 hashed value for the cache_key. Similarly, we need to artificially set the
    # language code on the request to 'en-us' to match the initial creation of the cache_key.
    # YMMV regarding the language code.
    request = HttpRequest()
    request.META = settings.CACHE_META_INVALIDATION
    request.LANGUAGE_CODE = "en-us"
    request.path = path

    try:
        cache_key = get_cache_key(request)
        if cache_key:
            if cache_key in cache:
                cache.delete(cache_key)
                return (True, "successfully invalidated")
            return (False, "cache_key does not exist in cache")
        raise ValueError("failed to create cache_key")
    except (ValueError, Exception) as err:
        return (False, err)


# pylint: disable=unused-argument
def is_panic_activated(request):
    return {"PANIC": cache.get(settings.PANIC_KEY)}


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
