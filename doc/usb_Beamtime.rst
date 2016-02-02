.. _usb_Beamtime:

Setting up your Beamtime
------------------------

Required Information
""""""""""""""""""""

 * a name for your beamtime object.  Let's assume it is ``mybt`` for now.
 * last name of the PI of the beamtime
 * SAF number

Goals of the Setup
""""""""""""""""""

#. Create your own beamtime python object.
#. Load into it all "beamtime-level" metadata.

Setup Steps
"""""""""""

 #. make sure you are familiar with the background information in :ref:`sb_overview` and :ref:`sb_icollection` 
 #. make sure you are in directory ``xpdUser``
 #. make sure you are in the ``collection`` ipython environment (see ``[collection]`` at the beginning of the line).  If you are not already in the ``collection`` environment, type ``icollection`` at the command prompt (see [here](:ref:`sb_icollection`) if you don't know what that means)
 #. time to create our own instance of Beamtime:

.. code-block:: python

  >>> mybt = Beamtime('<PIlastname>','<saf#>')
  output here
   
2. for example, for me it might be

.. code-block:: python

  >>> simonbt = Beamtime('Billinge','300438')
  output here



    >>> print('here')
    here

``icollection`` Typed at the command prompt from any directory.  This starts an ipython session and preloads all the packages needed for XPD data acquisition|

return to :ref:`bls`
