"""
Minimal frappe mock for standalone tests.
"""


class MockDB:


    def get_value(
        self,
        *args,
        **kwargs
    ):

        return None



    def exists(
        self,
        *args,
        **kwargs
    ):

        return False



db = MockDB()



def get_all(
    *args,
    **kwargs
):

    return []



def get_doc(
    *args,
    **kwargs
):

    return None


def whitelist(*args, **kwargs):
    def decorator(fn):
        return fn
    return decorator


def get_value(*args, **kwargs):
    return None


def throw(*args, **kwargs):
    raise Exception(args[0] if args else "throw")



def get_site_config(*args, **kwargs):
    return {}


conf = {}


def get_request_header(*args, **kwargs):
    return None


class _Cache:
    def get_value(self, *a, **kw): return None
    def set_value(self, *a, **kw): return None
    def delete_value(self, *a, **kw): return None
    def delete(self, *a, **kw): return None

def cache(*a, **kw):
    return _Cache()


session = type("S", (), {"user": "Guest", "data": {}})()
request = type("R", (), {"path": "/", "host": "erp.heshly.com", "headers": {}, "data": None, "get_json": lambda *a, **kw: {}})()
local = type("L", (), {"form_dict": {}, "qb": None})()
