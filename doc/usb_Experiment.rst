.. _usb_Experiment:

Setting up your Experiment Objects
----------------------------------

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

 1. make sure you are familiar with the background information in :ref:`sb_overview` 
    and :ref:`sb_icollection` 
 1. make sure you are in directory ``xpdUser``
 1. make sure you are in the ``collection`` ipython environment (see ``[collection]`` at the beginning of the line).  
    If you are not already in the ``collection`` environment, type ``icollection``
    at the command prompt (see [here](:ref:`sb_icollection`) if you don't know what that means)
 1. time to create our own instance of Beamtime:

.. code-block:: python

   >>> mybt = Beamtime('<PIlastname>','<saf#>')
   output here
   
2. for example, for me it might be

.. code-block:: python

   >>> simonbt = Beamtime('Billinge','300438')
   output here
   
Next: :ref:`usb_Experiment`

return to :ref:`xpdu`
