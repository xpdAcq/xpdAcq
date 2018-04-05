.. _usb_where:

Where did all my Sample and Scan objects go?????
------------------------------------------------

You just spent hours typing in metadata and creating
:ref:`sample <usb_experiment>` and :ref:`scan <usb_scan>`
objects, and now they have suddenly disappeared!  This
is a disaster!

As Douglas Adams taught us `DON'T PANIC` .  This is actually
`normal` (or at least `expected` ) behavior in xpdAcq.  Remember that
one of the design goals of the software project was to minimize
users' typing.  The design had to take into account that the
collection ``ipython`` environment is not so stable
(e.g., see :ref:`troubleshooting` ) and we should expect periodic
restarts of it.  How bad if we had to retype our metadata every
time?  So every time you create an xpdAcq acquisition object,
the details are saved to a file on the local hard-drive.  When
``xpdui`` is run, the main ``bt`` object (if it exists) is
automatically reloaded, but not the other acquisition objects.
But don't worry, they are all safe and sound.

.. _usb_bt_list:

bt.list() is your friends
--------------------------

To see what xpdAcquire acquisition objects you have available
to you, type ``bt.list()`` .  This lists the name and type of all
the acquisition objects that are on the hard-drive and available
to you....your objects: e.g.,

.. code-block:: python

  >>> bt.list()

  ScanPlans:
  0: 'ct_5'
  1: 'ct_30'
  2: 'ct_1'
  3: 'ct_10'
  4: 'ct_60'
  5: 'ct_0.1'

  Samples:
  0: Ni
  1: TiO2
  2: GaAs
  3: In0.5Ga0.5As
  4: In0.25Ga0.75As
  5: In0.75Ga0.25As
  6: InA

so they are all there, and we can get them, but we can no longer refer to them by the
assignment we used when we created them


To get them, we can explicitly reload them again or just use **index** of this object.
For example, consider the following sequence of code blocks:

.. code-block:: python

  >>> s1
  ---------------------------------------------------------------------------
  NameError                                 Traceback (most recent call last)
  <ipython-input-5-51081833a770> in <module>()
  ----> 1 s1

  NameError: name 's1' is not defined

Oh no, my ``s1`` sample object, which as my sample named `GaAs` , has disappeared!  ``bt.list()`` to the rescue...

.. code-block:: python

  >>> bt.list()

  ScanPlans:
  0: 'ct_5'
  1: 'ct_30'
  2: 'ct_1'
  3: 'ct_10'
  4: 'ct_60'
  5: 'ct_0.1'

  Samples:
  0: Ni
  1: TiO2
  2: GaAs
  3: In0.5Ga0.5As
  4: In0.25Ga0.75As
  5: In0.75Ga0.25As
  6: InA

That's it with a list index of 2, inside the Samples category. type object called.
Just to be sane, let's reload it. We can give it any name, it doesn't have to be
the same name as last time, so let's reload it as ``s1_again`` :

.. code-block:: python

  >>> s1_again = bt.samples['GaAs'] # e.g., the sample name is GaAs
  >>> s1_again
  {'bt_experimenters': ['Tim', 'Liu'],
   'bt_piLast': 'Billinge',
   'bt_safN': '300564',
   'bt_uid': 'fbb381c3',
   'bt_wavelength': 0.1832,
   'sa_uid': '4557b649',
   'sample_composition': {'As': 1.0, 'Ga': 1.0},
   'sample_name': 'GaAs'}


As you get used to this, you will realize that you don't actually have to reload
it at all, and can just refer directly to it.

You see that the *indexing method* acts exactly like (in fact it `is` ) the ``#`` th object
in the list returned by ``bt.list()`` . And it persists for your entire beamtime,
even if you hang up the entire software and have to have it restarted by one of the
IT guys.

Just remember.  First type ``bt.list()`` to locate the object you want, then use
object index to reference it based on categories. For example if I want to interrogate metadata
from ``ScanPlan`` object ``ct_5``, you can do:

.. code-block:: python

  >>> bt.scanplans.get_md(0)
  INFO: requested exposure time = 5 - > computed exposure time= 5.0
  {'detectors': ['pe1c'],
   'num_steps': 1,
   'plan_args': {'detectors': ['PE1C(name=pe1c)'], 'num': 1},
   'plan_name': 'count',
   'sp_computed_exposure': 5.0,
   'sp_num_frames': 50.0,
   'sp_plan_name': 'ct',
   'sp_requested_exposure': 5,
   'sp_time_per_frame': 0.1,
   'sp_type': 'ct',
   'sp_uid': 'bc3886a2-793a-4ee2-8269-a2ccb3030342'}

Don't forget the ``bt.list()`` first because your object may change its position
in the list over time.

As you probably noticed, we have ``bt.list()`` prints out two categories,
``ScanPlans`` and ``Samples``. The whole purpose of this is to make it easy to reference
desired objects.


.. _usb_gotchas:

bt.list() Gotchas
-----------------

Once you get used to this design we hope you will like it, but there are a
couple of important `Gotchas` that you should bear in mind that could lead to
confusion until you get used to them.

 #. If you create a `new` object with the same type and name as an existing one, the existing one will be **OVERWRITTEN** by the new one!  You will lose the old one forever.

    This is actually a feature of the code (we want each object to be unique and the only thing that makes it unique from one ``collection`` session to the next is its name and type).
    But please be careful about your naming! Why is it a feature?  You can use this to update an object by redefining it with the same name.

 #. At the time of writing, our xpdacq objects incorporate metadata from higher 
    in the stack (e.g., ``Sample`` inheriting ``Beamtime`` metadata) dynamically. 
    Any change on ``Beamtime`` metadata will automatically propagate down 
    to all ``Sample`` and ``ScanPlan`` objects.

go to :ref:`usb_scan`

go to :ref:`usb_running`

return to :ref:`xpdu`
