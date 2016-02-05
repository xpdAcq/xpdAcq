.. _usb_where:

Where did all my Sample and Scan objects go?????
------------------------------------------------

You just spent hours typing in metadata and creating
:ref:`sample <usb_experiment>` and :ref:`scan <usb_scan>`
objects, and now they have suddenly disappeared!  This
is a disaster!

As Douglas Adams taught us `DON'T PANIC` .  This is actually
`normal` (or at least `expected` ) behavior.  Remember that
one of the design goals of the software project was to minimize
users' typing.  The design had to take into account that the
collection ipython environment is not so stable 
(e.g., see :ref:`troubleshooting` ) and we should expect periodic
restarts of it.  How bad if we had to retype our metadata every
time?  So every time you create an xpdAcq acquisition object,
the details are saved to a file on the local hard-drive.  When
``icollection`` is run, the main ``bt`` object (if it exists) is
automatically reloaded, but not the other acquisition objects. 
But don't worry, they are all safe and sound.

.. _usb_bt_list:

bt_list() and bt_get() are your friends
---------------------------------------

To see what xpdAcquire acquisition objects you have available 
to you, type ``bt.list()`` .  This lists the name and type of all 
the acquisition objects that are on the hard-drive and available
to you....your objects: e.g., 

.. code-block:: python

  >>> bt.list()
  bt object bt has list index  0
  ex object InGaAsAlloyPD has list index  1
  ex object ProteinFolding has list index  2
  sa object GaAs has list index  3
  sa object IGA75-25 has list index  4
  sa object In0.25Ga0.75As has list index  5
  sa object InAs has list index  6
  sa object InGaAs-5050 has list index  7
  Use bt.get(index) to get the one you want

so they are all there, and we can get them, but we can no longer refer to them by the
assignment we used when we created them (remember we used ``s1`` , ``s2`` and so on)

To get them we use ``bt.get()`` .  We can explicitly reload them again
or usually just use ``bt.get(#)`` where ``#`` is the list index (a number) as a  for example,
to refer to them directly. For example, consider the following sequence of code blocks:

.. code-block:: python
  
  >>> s1
  ---------------------------------------------------------------------------
  NameError                                 Traceback (most recent call last)
  <ipython-input-5-51081833a770> in <module>()
  ----> 1 s1

  NameError: name 's1' is not defined

Oh no, my ``s1`` sample object, which as my sampled named `GaAs` , has disappeared!  ``bt.list()`` to the rescue...

.. code-block:: python

  >>> bt.list()
  bt object bt has list index  0
  ex object InGaAsAlloyPD has list index  1
  ex object ProteinFolding has list index  2
  sa object GaAs has list index  3
  sa object IGA75-25 has list index  4
  sa object In0.25Ga0.75As has list index  5
  sa object InAs has list index  6
  sa object InGaAs-5050 has list index  7
  Use bt.get(index) to get the one you want
  
That's it with a list index of 3, the ``sa`` sample type object called ``GaAs`` .
Just to be sane, let's reload it. We can give it any name, it doesn't have to be
the same name as last time, so let's reload it as ``s1_again`` :

.. code-block:: python

  >>> s1_again = bt.get(3)
  >>> s1.name
  'GaAs'

As you get used to this, you will realize that you don't actually have to reload
it at all, and can just refer directly to it.  For example, type ``bt.get(3).md``
and see what you get

.. code-block:: python

  >>> bt.get(3).md
  {'bt_experimenters': {('Chia-Hao', 'Liu'), ('Simon', 'Billinge')},
   'bt_piLast': 'Billinge',
   'bt_safN': 300256,
   'bt_uid': '9b0c5878-cba4-11e5-8984-28b2bd4521c0',
   'bt_wavelength': 0.1818,
   'ex_name': 'ProteinFolding',
   'ex_uid': 'c89120dc-cbc8-11e5-ac9b-28b2bd4521c0',
   'sa_name': 'GaAs',
   'sa_uid': '7c6f5fc6-cbca-11e5-bec0-28b2bd4521c0'}


You see that ``bt.get(#)`` acts exactly like (in fact it `is` ) the ``#`` th object
in the list returned by ``bt.list()`` . And it persists for your entire beamtime,
even if you hang up the entire software and have to have it restarted by one of the
IT guys.

Just remember.  First type ``bt.list()`` to locate the object you want, then type
``bt.get(#)`` to get it.  Don't forget the ``bt.list()`` first because your object
may change its position in the list over time.

A little hint too.  If it is late in your beamtime and you have hundreds of those objects, you can
select to list them by type, e.g. if you just want the Sample (``sa`` ) type objects then
type ``bt.list('sa')`` :

.. code-block:: python

  >>> bt.list('sa')
  sa object GaAs has list index  3
  sa object IGA75-25 has list index  4
  sa object In0.25Ga0.75As has list index  5
  sa object InAs has list index  6
  sa object InGaAs-5050 has list index  7
  Use bt.get(index) to get the one you want

Make sure to refer to that object by the written index number and not where you see it on the returned list!

.. _usb_gotchas:

bt_list() and bt_get() Gotchas
------------------------------

Once you get used to this design we hope you will like it, but there are a 
couple of important `Gotchas` that you should bear in mind that could lead to
confusion until you get used to them.

 #. If you create a `new` object with the same type and name as an existing one, the existing one will be **OVERWRITTEN** by the new one!  You will lose the old one forever.
 
    This is actually a feature of the code (we want each object to be unique and the only thing that makes it unique from one ``collection`` session to the next is its name and type). But please be careful about your naming! Why is it a feature?  You can use this to update an object by redefining it with the same name.
 
 #. Objects may change their position in the ``bt.list()`` as new objects are created.  Just because the object you want was in position ``4`` before, doesn't mean it will be now. **So get used to always typing** ``bt.list()`` **FIRST then** ``bt.get()`` .

  
return to :ref:`xpdu`

