**Added:**

* Add `CalibPreprocessor` to record calibration data and put the data in the `calib` data stream.

* Add `DarkPreprocessor` to add taking dark frame steps into the plan, snapshot the dark frame and add it in the `dark` data stream.

* Add `ShutterPreprocessor` to open the shutter before the trigger of detector and close it after the wait.

* Add `xpdcaq.simulators` module. It contains the simulated devices for testing.

* Add `UserInterface` to create the objects necessary in the ipython session.

**Changed:**

* <news item>

**Deprecated:**

* `periodic_dark` and `take_dark` are no longer used in `CustomizeRunEngine`. The dark frame is taken care by `DarkPreprocessor`.

* Setting `frame_acq_time` no longer changes the detector acquire time immmediately. The value will be read and used to set the acquire time when using the xpdacq customizd plans, like `ct`, `Tlist`, `Tramp` and `tseries`.

* `CustomizedRunEngine` no longer loads the calibration data at the `open_run`. The calibration data is handled by `CalibPreprocessor`.

* `auto_load_calib` no longer used in the global setting since the `CustomizedRunEngine` no longers loads the calibration data.

* `inner_shutter_control` is no longer used in the xpdacq customized plans. The shutter control is given to `ShutterPreprocessor`.

**Removed:**

* <news item>

**Fixed:**

* Skip the outdated tests and make CI tests run smoothly.

**Security:**

* <news item>
