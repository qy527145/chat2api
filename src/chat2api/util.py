import hashlib
import time
from collections import OrderedDict


def now():
    return int(time.time())


def md5(msg: str):
    if isinstance(msg, str):
        hash_obj = hashlib.md5()
        hash_obj.update(msg.encode())
        return hash_obj.hexdigest()


class LRUCache:
    def __init__(self, capacity, key_hash_func=md5):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.key_hash_func = key_hash_func

    def __getitem__(self, key):
        if self.key_hash_func:
            key = self.key_hash_func(key)
        if key not in self.cache:
            return None
        else:
            # 将元素移到字典末尾表示最近访问
            self.cache.move_to_end(key)
            return self.cache[key]

    def get(self, key, default=None):
        value = self[key]
        return value if value is not None else default

    def __setitem__(self, key, value):
        if self.key_hash_func:
            key = self.key_hash_func(key)
        if key in self.cache:
            # 更新键值，并将元素移到字典末尾
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            # 弹出字典开头的元素，即最久未访问的元素
            self.cache.popitem(last=False)
