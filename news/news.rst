**Added:**

* Add `xpdacq.factory.BasicPlans` for the multi-detector plan for both XRD and PDF data collection in one run.

* Add `xpdacq.factory.MultiDistPlans` for the moving detector measurement for both XRD and PDF data collection in one run.

* Add `xpdacq.devices.CalibrationData`, a class to store the calibration data of a detector in configuration attributes.

* Add `xpdacq.beamtime.load_calibration_md`, a helper function to load calibration data

* Add `xpdacq.beamtime.count_with_calib`, a helper function to build multiple-calibration plan

**Changed:**

* <news item>

**Deprecated:**

* <news item>

**Removed:**

* <news item>

**Fixed:**

* Fix the bugs for python 3.9 ``TypeError: dict.popitem() takes no arguments (1 given)``.

* Fix the bugs for xpdconf 0.4.5 that the default calibration metadata file is poni file instead of yaml file.

**Security:**

* <news item>
