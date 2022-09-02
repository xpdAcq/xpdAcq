Automatic Shutter Control
=========================

In this section, the automatic shutter control in ``xpdAcq`` is
introduced.

ShutterPreprocessor
-------------------

The automatic shutter control is realized by the
``ShutterPreprocessor``.

They are registered in the ``xrun.shutter_preprocessors`` list.

.. code:: ipython3

    xrun.shutter_preprocessors




.. parsed-literal::

    [<ShutterPreprocessor for detector>,
     <ShutterPreprocessor for detector1>,
     <ShutterPreprocessor for detector2>]



There is an one to one mapping between a shutter preprocessors to a
detector and a many to one mapping between shutter preprocessors to the
fast shutter.

Logic
-----

When the ``ShutterPreProcessor`` finds that the ``detector`` is
triggered to take a light frame (not labled by ``dark_group_prefix``).
Then, it will add the open and close shutter into the plan. The logic is
shown in the peseudo code below.

::

   if (shutter is closed currently):
       open the shutter
   if (delay > 0):
       wait for seconds
   trigger the detector
   wait for the detector to finish counting
   if (shutter is opened currently):
       close the shutter

Usage
-----

By using the ``ShutterPreprocessor``, users can use all the predefined
plan in the ``bluesky.plans`` without worrying about the shutter
control. For example, when users would like to collect one light frame,
they just need to run the ``bluesky.plans.count``.

.. code:: ipython3

    xrun(0, bp.count([detector]))


.. parsed-literal::

    INFO: Current filter status
    INFO: flt1 : In
    INFO: flt2 : In
    INFO: flt3 : In
    INFO: flt4 : In
    
    
    Transient Scan ID: 1     Time: 2022-04-07 12:29:55
    Persistent Unique Scan ID: '95cc5a91-2832-45b3-95df-630c8563414c'
    New stream: 'dark'
    New stream: 'primary'
    +-----------+------------+
    |   seq_num |       time |
    +-----------+------------+
    |         1 | 12:29:57.1 |
    +-----------+------------+
    generator count ['95cc5a91'] (scan num: 1)




.. parsed-literal::

    ('95cc5a91-2832-45b3-95df-630c8563414c',)



The shutter will open automatically before the collection and close
after that.

Here is another example where users would like to collect several light
frames at different temperatures.

.. code:: ipython3

    xrun(0, bp.scan([detector], cryostream, 300, 500, 3))


.. parsed-literal::

    INFO: Current filter status
    INFO: flt1 : In
    INFO: flt2 : In
    INFO: flt3 : In
    INFO: flt4 : In
    
    
    Transient Scan ID: 2     Time: 2022-04-07 12:32:39
    Persistent Unique Scan ID: '3e72d2a9-c6ef-4278-81da-db91bd28e35c'
    New stream: 'dark'
    New stream: 'primary'
    +-----------+------------+-------------+
    |   seq_num |       time | temperature |
    +-----------+------------+-------------+
    |         1 | 12:32:41.1 |     300.000 |
    |         2 | 12:32:42.1 |     400.000 |
    |         3 | 12:32:43.1 |     500.000 |
    +-----------+------------+-------------+
    generator scan ['3e72d2a9'] (scan num: 2)




.. parsed-literal::

    ('3e72d2a9-c6ef-4278-81da-db91bd28e35c',)



During the run, the shutter will open before the image collection and
close after that at every temperature point. Users don’t need to worry
that the shutter keeps open during the temperature ramping.

Enable and Disable
------------------

The ``ShutterPreprocessor`` can be disabled by calling ``disable``.
After disabled, it will do noting to the users’ plans.

.. code:: ipython3

    xrun.shutter_preprocessors[0].disable()

It can be enabled again by calling ``enable``.

.. code:: ipython3

    xrun.shutter_preprocessors[0].enable()

ShutterConfig
-------------

The open and close state are defined in the ``ShutterConfig`` object.

This object is a private attribute of ``ShutterPreprocessor`` should be
changed by users but the values in it can be reference to users when
they are writing their own shutter control in the plan.

.. code:: ipython3

    xrun.shutter_preprocessors[0]._shutter_config




.. parsed-literal::

    ShutterConfig(shutter=FastShutter(name='shutter', value='closed', timestamp=1649349163.1470232), open_state='open', close_state='closed', delay=0.0)


