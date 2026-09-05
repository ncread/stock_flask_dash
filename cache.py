from cachetools import TTLCache

price_cache = TTLCache(maxsize=500, ttl=60*60*12) #12 hrs
feature_cache = TTLCache(maxsize=500, ttl=1800) #30 mins