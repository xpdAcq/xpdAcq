**Added:** None

**Changed:**

* Reduce summary field of callable argument in ``ScanPlan`` with only
  its ``__name__``. Before it use ``__repr__`` which includes hash and
  special characters that is prone to generate illegal filename for yaml.

**Deprecated:** None

**Removed:** None

**Fixed:**

* ``per_step`` argument in ``Tlist``. Before this argument is always
  overridden by default.

**Security:** None
