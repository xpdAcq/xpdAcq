New calibration data storage method
===================================

What is calibration?
--------------------

The calibration is a process to obtain the geometry status of the
detector and the beam spot on it. By fitting the diffraction pattern of
a standard material like Ni with the knowledge of wavelength and
D-spacing of the material, we will obtain the sample-detector distance,
the orientation of the detector and the position of the center of the
beam on the detector. These information is important for the azimuthal
integration of the diffraction image.

What is the old way to store the calibraiton data? Why is it not good enough?
-----------------------------------------------------------------------------

We assume that there is only one detector used in our measurement and
this detector never moves in one measurement. We can only move the
detector and recalib it outsides measurements. Thus, in the old way, we
use a file as a cache for the calibration data. Every time a calibration
is done, the calibration data will overwrite the former data in that
file.

However, this assumption is not always held. For example, if the user
would like to use two detectors, one for the near field and the other
for far field, the old method doesn’t hold. Also, if the user
accidentally deletes the file, the software will crash.

What is the new way?
--------------------

It is better to store the calibration data as a part of the
configuration of the detector. We can view the calibration data as the
status of how the detector is set right now just like frame rate.

In ophyd, the communication to the hardware of a detector is done by a
virtual python class ``Device``. It provides us the convenience to store
the calibration data inside the detector. We will descripe how it is
done in the later sections.

Add the compenent of calibration data to a detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, we define a class ``DetectorWithCalib`` based on the
``DiffractionDetector`` class. You can change the
``DiffractionDetector`` to the class of the detector that you defined in
your script. The ``DetectorWithCalib`` has a component ``calib`` and
this is a part of the configuraion of this detector.

.. code:: ipython3

    from xpdacq.devices import CalibrationData
    from bluesky_darkframes.sim import DiffractionDetector, Shutter
    from ophyd.device import Component as Cpt
    from ophyd import Kind
    
    
    class DetectorWithCalib(DiffractionDetector):
        calib = Cpt(CalibrationData, kind=Kind.config)

.. code:: ipython3

    detector = DetectorWithCalib(name="area_detector")
    shutter = Shutter(name="fast_shutter")

Run the calibration
-------------------

We create a python class ``BasicPlans`` and then use the class method
``calibrate`` to run the calibration. A gui will show up for the user to
do the calibration. Here the arguments of the method is a list of
detectors to collect the images of diffractions and a list of the
calibration data components inside the detectors to store the
calibration result.

Here, we use ``bt_wavelength=1.6`` to tell the software the wavelength
of the beam.

.. code:: ipython3

    from databroker import Broker
    from bluesky import RunEngine
    from xpdacq.planfactory import BasicPlans
    
    
    db = Broker.named("temp")
    RE = RunEngine()
    RE.md["bt_wavelength"] = 1.6
    RE.subscribe(db.insert)
    myplans = BasicPlans(shutter=shutter, shutter_open=0, shutter_close=1, db=db)
    plan = myplans.calibrate([detector], [detector.calib])
    RE(plan)




.. parsed-literal::

    ('d0c9ab1a-72df-4ade-bd98-6217afbc5850',)



Please do not change the file name of the poni file in the GUI.
Otherwist, the software will fail to identify where the calibration
result is.

Where is the calibration data?
------------------------------

The calibration data will be saved in three spaces: (a) the ``calib``
componenet inside the detector (b) the ``.poni`` file inside
``xpdacq_calib`` folder.

The calib component
~~~~~~~~~~~~~~~~~~~

The calibration data is a part of the configuration of the detector and
can be read by ``read_configuration`` method.

.. code:: ipython3

    detector.calib.read_configuration()




.. parsed-literal::

    OrderedDict([('area_detector_calib_dist',
                  {'value': 0.027647816455789107, 'timestamp': 1619201329.27096}),
                 ('area_detector_calib_poni1',
                  {'value': 0.20325088237193026, 'timestamp': 1619201329.272158}),
                 ('area_detector_calib_poni2',
                  {'value': 0.20070643030746954, 'timestamp': 1619201329.272973}),
                 ('area_detector_calib_rot1',
                  {'value': 0.014065256151799823, 'timestamp': 1619201329.273674}),
                 ('area_detector_calib_rot2',
                  {'value': -0.021405344966918656, 'timestamp': 1619201329.27525}),
                 ('area_detector_calib_rot3',
                  {'value': -0.001561273022415835,
                   'timestamp': 1619201329.2759628}),
                 ('area_detector_calib_pixel1',
                  {'value': 0.002, 'timestamp': 1619201329.277357}),
                 ('area_detector_calib_pixel2',
                  {'value': 0.002, 'timestamp': 1619201329.27779}),
                 ('area_detector_calib_detector',
                  {'value': 'Perkin detector', 'timestamp': 1619201329.2764459}),
                 ('area_detector_calib_wavelength',
                  {'value': 1.6000000000000002e-10,
                   'timestamp': 1619201329.27694})])



The poni file
-------------

The caibration component in the detector can only keep the latest the
calibration result. The a history of calibration result is cached in a
folder ``xpdacq_calib``. The following code shows an example of what are
in the folder.

.. code:: ipython3

    !tree xpdacq_calib


.. parsed-literal::

    [01;34mxpdacq_calib[00m
    ├── 3ac4b669-a692-4849-a65a-b853fe1362c1_area_detector_image.poni
    ├── 3ac4b669-a692-4849-a65a-b853fe1362c1_area_detector_image.tiff
    ├── d0c9ab1a-72df-4ade-bd98-6217afbc5850_area_detector_image.poni
    └── d0c9ab1a-72df-4ade-bd98-6217afbc5850_area_detector_image.tiff
    
    0 directories, 4 files


Where will the calibration data go?
-----------------------------------

The calibration data will be saved in the descriptor document of a
stream.

.. code:: ipython3

    RE(myplans.count([detector]))




.. parsed-literal::

    ('77cdf1ba-db2a-430a-8100-d7ece2954b6c',)



.. code:: ipython3

    run = db[-1]
    run.descriptors[0]




.. raw:: html

    
    <table>
    
      <tr>
        <th> configuration </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector </th>
        <td>
    
            <table>
    
      <tr>
        <th> data </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector_calib_detector </th>
        <td>
    
    
                Perkin detector
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_dist </th>
        <td>
    
    
                0.027647816455789107
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_pixel1 </th>
        <td>
    
    
                0.002
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_pixel2 </th>
        <td>
    
    
                0.002
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_poni1 </th>
        <td>
    
    
                0.20325088237193026
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_poni2 </th>
        <td>
    
    
                0.20070643030746954
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot1 </th>
        <td>
    
    
                0.014065256151799823
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot2 </th>
        <td>
    
    
                -0.021405344966918656
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot3 </th>
        <td>
    
    
                -0.001561273022415835
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_wavelength </th>
        <td>
    
    
                1.6000000000000002e-10
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> data_keys </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector_calib_detector </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                string
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_detector
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_dist </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_dist
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_pixel1 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_pixel1
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_pixel2 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_pixel2
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_poni1 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_poni1
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_poni2 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_poni2
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot1 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_rot1
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot2 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_rot2
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot3 </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_rot3
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_wavelength </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                number
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_calib_wavelength
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> timestamps </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector_calib_detector </th>
        <td>
    
    
                1619201329.2764459
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_dist </th>
        <td>
    
    
                1619201329.27096
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_pixel1 </th>
        <td>
    
    
                1619201329.277357
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_pixel2 </th>
        <td>
    
    
                1619201329.27779
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_poni1 </th>
        <td>
    
    
                1619201329.272158
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_poni2 </th>
        <td>
    
    
                1619201329.272973
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot1 </th>
        <td>
    
    
                1619201329.273674
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot2 </th>
        <td>
    
    
                1619201329.27525
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_rot3 </th>
        <td>
    
    
                1619201329.2759628
    
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_calib_wavelength </th>
        <td>
    
    
                1619201329.27694
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> data_keys </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector_exposure_time </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                integer
    
    
        </td>
      </tr>
    
      <tr>
        <th> object_name </th>
        <td>
    
    
                area_detector
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:area_detector_exposure_time
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> area_detector_image </th>
        <td>
    
            <table>
    
      <tr>
        <th> dtype </th>
        <td>
    
    
                array
    
    
        </td>
      </tr>
    
      <tr>
        <th> external </th>
        <td>
    
    
                FILESTORE
    
    
        </td>
      </tr>
    
      <tr>
        <th> object_name </th>
        <td>
    
    
                area_detector
    
    
        </td>
      </tr>
    
      <tr>
        <th> shape </th>
        <td>
    
    
                [200, 200]
    
    
        </td>
      </tr>
    
      <tr>
        <th> source </th>
        <td>
    
    
                SIM:image
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> hints </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector </th>
        <td>
    
            <table>
    
      <tr>
        <th> fields </th>
        <td>
    
    
                []
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> name </th>
        <td>
    
    
                primary
    
    
        </td>
      </tr>
    
      <tr>
        <th> object_keys </th>
        <td>
    
            <table>
    
      <tr>
        <th> area_detector </th>
        <td>
    
    
                ['area_detector_exposure_time', 'area_detector_image']
    
    
        </td>
      </tr>
    
            </table>
    
        </td>
      </tr>
    
      <tr>
        <th> run_start </th>
        <td>
    
    
                77cdf1ba-db2a-430a-8100-d7ece2954b6c
    
    
        </td>
      </tr>
    
      <tr>
        <th> time </th>
        <td>
    
    
                28 minutes ago (2021-04-23T14:10:18.666415)
    
    
        </td>
      </tr>
    
      <tr>
        <th> uid </th>
        <td>
    
    
                1c692e48-0845-4478-9a4a-3a2fec50eda4
    
    
        </td>
      </tr>
    
    </table>


