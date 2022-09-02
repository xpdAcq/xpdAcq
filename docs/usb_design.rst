An overhaul at v1.1.0
=====================

I made an important update at v1.1.0. I will introduce what I did, why I did it, and what I achieved by doing it. In principle, I didn't change any behaviors in the use cases for previous versions. However, if you developed any software based on the API of the XpdAcq, I recommend you reading this section.

Automated Processes
-------------------

The XpdAcq automated three important processes in the x-ray scattering experiments: (1) open and close shutter (2) take dark frame and save it (3) run calibration and save the result.

I will first show how the previous XpaAcq did it, why it was not good enough, and then demonstrate what is like after my update. The details of the code are shown in the later sections. Here, I only introduced the logics. I also shows the new fucntion of mask injection in the last paragraph.

Shutter Control
^^^^^^^^^^^^^^^

Everytime a light frame is going to be taken, the shutter should open and then close after this is done. This behavior is programmed in the beamtime scan plans in the previous XqdAcq. However, there is an issue doing it this way. If users would like to do anything other than the XpaAcq programmed, they need to explicitly write the open and close shutter in their plan. This is quite hard for usres without the knowledge to the beamline and python programming skills.

I would like to make the control of the shutter taken cared in a more automated way. I developed a shutter preprocessor to realize it. This preprocessor reads the users' plan, and if it sees that a light frame is going to be taken, it will open the shutter before it, wait for a time specified by the user, and then continue the plan. When it finds that the light frame has been taken, it will close the shutter. This preprocessor is subcribed in the `xrun.shutter_preprocessors`.

Because of this preprocessor, users do not need to worry about the shutter control. They can use any helper functions in the `bluesky.plans` or write their own plan without knowing what is the name of the shutter and how it opens and closes.

Dark Frame
^^^^^^^^^^

The preivous XpdAcq took dark frame automatically before every bluesky run. It realized it by using a preprocessor. This preprocessor will read users' bluesky plan step by step and then if it finds a `open_run`, it will decide whether a new dark frame needs to be taken. If there is such a need, it will add a step in users' plan to close the shutter, take the dark frame, save it in database, inject the metadata about how to find the dark frame, and finally open the shutter again.

You may already find the problems in this method.

* Because it saves the dark frame in a separate individual document, the data analysis servers must query the database everytime it needs to do a dark subtraction.
* It force users to user no more than one dark frame for the entire run, and thus cannot satify the needs for multiple dark frame when the experiment is long.
* The code of this preprocessor is hard coded in the `xrun`. It makes the development hard. This dark frame preprocessor can only be used for one detector.
* This only take care of one detector and if the detector is changed, it cannot distinguish their dark frame.

I deprecate this dark frame preprocessor and made a new one.

* It save the dark frame in its cache, and injected the data in the `dark` event stream.
* It check the necessity to take dark frame before every light frame is taken. It allows users to fully control how their dark frame was taken in an experiment.
* This one was separated from the `xrun`. It can be subcribed in a list `xrun.dark_preprocessors`. One dark frame preprocessor takes care of one detector. 
* It allows the usage of multiple detectors with automatic dark frame without mixing their dark frame data, which the old preprocessor did.

Calibration
^^^^^^^^^^^

The calibration in preivous xpdacq was also done by preprocessing the plan. It first saves the calibration results in a poni file and then read and inject the data in this poni file in the start documents. There are some problems with this method.

* One bluesky run only has one start document. It force the calibration data to be constant in the whole runk, which is not always the case. An typical example is to move the detector back and forth to take far field image and near field image.
* It assumes that there is only one detector. If there is another detector, it cannot distinguish which calibration data to use.
* It only keeps the latest calibration data in the record. Users needs to do calibration again even when they just change the experiment setup back to the previous setup.
* This preprocessing is hard coded in the `xrun`.

I designed the calibration preprocessor to solve these problems. The calibration preprocessor is separated from the `xrun` and it is subcribed in the list `xrun.calib_preprocessors` to take effect. It hosts a cache of the calibration data. When a light frame is going to be taken, it will check the position of the detectors (or other devices specified by the user), find the calibration data, and inject the data in the `calib` even stream. It enables the users to move the detector or use multiple detector during the experiments without worrying that calibration data is not correct. It is also quicker because it doesn't needs to read a file every time. It is also compatible with the previous one. It saves the latest result in a poni file so that the latest results are always loaded if `bsui` is restarted.

Mask
^^^^

In the past, users cannot give their own masks in the data processing. They can only expect the automasking gives them a good results. But now, because of the mask preprocessor, the users can give any masks they want. The mask preprocessor will inject the mask data in `mask` event stream. This event stream can be used again by the data analysis server.

Final Goal
----------

My ultimate goal of the development is to fulfill the initial motivation of the XpdAcq, that is, to make bluesky easy to use in the x-ray scattering experiments. The previous version solved this problem but it left the room for improvement. As a frequent issue, every time the users would like to run some experiments out of the scope of the helper functions in the `beamtime` module, I need to write a pretty long script for them. After this improvements, the users can actually use the well developed bluesky library without any more knowledge or skills.

For example, in the past, the users needs to worry about all kinds of things like calibration, shutter or dark frame when they just would like to measure diffraction images at a series temperature at a near field for PDF and a far field for XRD. Now, they just write the code below and things will work out for them.

.. code:: python

    import bluesky.plans as bp

    plan = bp.grid_scan([detector], temperature, low, high, num_of_points, detector_z, near_field, far_field, 2)
    xrun(sample, plan)

