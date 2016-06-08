from contextlib import contextmanager


class ValidatedDict(dict):
    """
    This a dict with a `validate` method that may raise any exception.

    The dict it validation on initialization and any time its contents
    are changed. If a change is illegal, it is reverted an the exception
    from `validate` is raised. Thus, it is impossible to put the dict
    into an invalid state.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate()

    def clear(self):
        original = dict(self)
        super().clear()
        try:
            self.validate()
        except:
            super().update(original)
            raise

    def pop(self, key):
        val = super().pop(key)
        try:
            self.validate()
        except:
            super().__setitem__(key, val)
            raise

    def popitem(self):
        key, val = super().popitem()
        try:
            self.validate()
        except:
            super().__setitem__(key, val)
            raise

    def setdefault(self, key, val):
        original = dict(self)
        super().setdefault(key, val)
        try:
            self.validate()
        except:
            super().update(original)
            raise

    def update(self, *args, **kwargs):
        original = dict(self)
        super().update(*args, **kwargs)
        try:
            self.validate()
        except:
            super().clear()
            super().update(original)
            raise

    def __setitem__(self, key, val):
        super().__setitem__(key, val)
        try:
            self.validate()
        except:
            super().__delitem__(key)
            raise

    def __delitem__(self, key):
        val = self[key]
        super().__delitem__(key)
        try:
            self.validate()
        except:
            super().__setitem__(key, val)
            raise

    def validate(self):
        pass

@contextmanager
def safe_validate(d, key):
    tmp = d[key]
    d[key] = d[key]['uid']
    try:
        yield
    finally:
        d[key] = tmp

@contextmanager
def dereference(d, key):
    tmp = d[key]
    d[key] = d[key]['uid']
    try:
        yield
    finally:
        d[key] = tmp
