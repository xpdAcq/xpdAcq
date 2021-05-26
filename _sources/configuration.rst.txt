.. _configuration:

Configuration
=============

Configuration of the globals is driven by a configuration file in any of the
following locations

    .. code-block:: none

       ~/.config/acq
       <python>/etc/acq
       /etc/acq

Where ``<python>`` is the path to the python executable being run.

Here is an example configuration file:

    .. code-block:: yaml

       ARCHIVE_BASE_DIR_NAME: .userBeamtimeArchive
       ARCHIVE_ROOT_DIR: ~/acqsim/archive
       BASE_DIR: ~/acqsim
       BEAMLINE_HOST_NAME: [xf28id2-ws2, xf28id2-ws3]
       BEAMLINE_ID: 28-ID-2
       BLCONFIG_DIR_NAME: xpdConfig
       BLCONFIG_NAME: XPD_beamline_config.yml
       CALIB_CONFIG_NAME: xpdAcq_calib_info.yml
       DARK_WINDOW: 3000
       FACILITY: sim
       FRAME_ACQUIRE_TIME: 0.1
       GLBL_YAML_NAME: glbl.yml
       GROUP: sim
       HOME_DIR_NAME: xpdUser
       IMAGE_FIELD: pe1_image
       OWNER: sim
       SIMULATION: true
       SHUTTER_CONF: {close: 0, open: 60}

More examples can be found in the `examples folder <https://github.com/xpdAcq/xpdAcq/tree/master/xpdacq/examples>`_