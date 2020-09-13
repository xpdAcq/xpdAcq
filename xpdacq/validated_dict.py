class ValidatedDictLike(dict):
    """
    This a dict with a `validate` method that may raise any exception.

    The dict it validation on initialization and any time its contents
    are changed. If a change is illegal, it is reverted an the exception
    from `validate` is raised. Thus, it is impossible to put the dict
    into an invalid state.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.validate()
        except ValidationError:
            raise ValidationError("Validation failed. Unable to create ValidatedDictLike.")

    def clear(self):
        original = dict(self)
        super().clear()
        try:
            self.validate()
        except ValidationError:
            super().update(original)
            raise ValidationError("Validation failed. Unable to clear.")

    def pop(self, key):
        val = super().pop(key)
        try:
            self.validate()
        except ValidationError:
            super().__setitem__(key, val)
            raise ValidationError("Validation failed. Unable to pop {}".format(key))

    def popitem(self):
        key, val = super().popitem()
        try:
            self.validate()
        except ValidationError:
            super().__setitem__(key, val)
            raise ValidationError("Validation failed. Unable to popitem {}".format(key))

    def setdefault(self, *args, **kwargs):
        original = dict(self)
        super().setdefault(*args, **kwargs)
        try:
            self.validate()
        except ValidationError:
            super().update(original)
            raise ValidationError("Validation failed. Unable to setdefault.")

    def update(self, *args, **kwargs):
        original = dict(self)
        super().update(*args, **kwargs)
        try:
            self.validate()
        except ValidationError:
            super().clear()
            super().update(original)
            raise ValidationError("Validation failed. Unable to update.")

    def __setitem__(self, key, val):
        super().__setitem__(key, val)
        try:
            self.validate()
        except ValidationError:
            super().__delitem__(key)
            raise ValueError("Validation failed. Unable to set {}: {}".format(key, val))

    def __delitem__(self, key):
        val = self[key]
        super().__delitem__(key)
        try:
            self.validate()
        except ValidationError:
            super().__setitem__(key, val)
            raise ValueError("Validation failed. Unable to delete {}".format(key))

    def validate(self):
        pass


class ValidationError(Exception):
    pass
