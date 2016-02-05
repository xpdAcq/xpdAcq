.. _usb_Beamtime:

Setting up your Beamtime
------------------------

This should have been carried out by the beamline responsible.  To check all is ok,
carry out the following steps:

 #. Check you are in the collection environment
 #. Type ``bt``.  It should return an ``xpdacq.beamtime.Beamtime`` object.  If not, please contact your beamline responsible.
 
.. code-block:: python
 
  >>> bt
  <xpdacq.beamtime.Beamtime at 0x4b112b0>
  
This object contains some critical information about your beamtime.  You can investigate what is inside...

 #. To see what is inside any such object place a dot after bt and hit `tab`
 
.. code-block:: python
  
  >>> bt.
  bt.export    bt.list        bt.md     bt.type
  bt.get       bt.loadyamls   bt.name
  
It will list all the things you can investigate. for example, in our case:
   
.. code-block:: python
  
  >>> bt.name
  'bt'
  >>> bt.type
  'bt'

So this is a beamtime (`'bt'`) type of object with name `'bt'`.  More interesting
is the metadata it contains:

.. code-block:: python
  
  >>> bt.md
 {'bt_experimenters': {('Chia-Hao', 'Liu'), ('Simon', 'Billinge')},
 'bt_piLast': 'Billinge',
 'bt_safN': 300256,
 'bt_uid': '9b0c5878-cba4-11e5-8984-28b2bd4521c0',
 'bt_wavelength': 0.1818}

The instrument responsible loaded an initial version of ``bt`` with information 
from the Safety Approval Form (SAF) form: the PI last name, the SAF number
and the experimenters.

When the beamtime object was created it created its very own unique-ID, the ``bt_uid``.  
As long as you use the XPD acquisition software, every scan you make during your beamtime
will be contain this ``'bt_uid'`` metadata field with the same uid value.
This can be searched for later in the scan headers and used to find all the data
collected during your beamtime, for example.

.. code-block:: python
 
  >>> bt = Beamtime('Billinge',300256,0.1818,{('Simon','Billinge'),('Chia-Hao','Liu')})

 
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
 #. make sure you are in the ``collection`` ipython environment (e.g., see ``(collection)`` at the beginning of the command line).  If you are not already in the ``collection`` environment, type ``icollection`` at the command prompt (see :ref:`here <sb_icollection>` if you don't know what that means)
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
