.. _usb_experiment:

Setting up your XPD acuisition objects
--------------------------------------

Overview
""""""""

The basic workflow is 

 #. Set up xpdAcq `experiment-sample` objects. These contain information about the samples and experimental conditions.
 #. Set up xpdAcq `scan` objects.  These contain information used to run the scan, and metadata about the scan.
 #. Run scans by passing one ``sample`` and one ``scan`` object to the various available `run` functions. Data will be measured and saved to the NSLS-II file-store with all the metadata in the objects saved with it.
 #. Extract scans and data that you want from the data-store by searching on the metadata, selecting the data you want and extracting it in the form you want it (e.g., tiff files)
 #. Analyze the data, by integrating images to 1D diffraction patterns, F(Q), and PDFs, subtracting backgrounds, plotting and fitting models
 #. Export all the data, both raw tiffs and analyzed data, that you want.
 
Note that the raw data, and metadata, will be stored indefinitely by NSLS-II, and can be searched for and extracted at any time in the future.

Hierarchy of experiment-sample objects
""""""""""""""""""""""""""""""""""""""

The goal of the xpd Acquisition software is to save data with as much accurate metadata
as possible with as little user-typing as possible.  To do this we associate
metadata with appropriate levels of the beamtime hierarchy laid out in :ref:`sb_icollection`.
In :ref:`usb_beamtime` we discussed setting up the main ``Beamtime`` object.  Here we set
up the an object at the next level down in hierarchy, ``Experiment``.

The basic syntax is ``e=Experiment(arg1,arg2,...)``, where the ``args`` are the arguments
or parameters of the object, but it is always helpful to have a little reminder
of what are the required and optional arguments of this object.  ipython offers a
handy feature that you can type a ``?`` instead of the parentheses after a function and
ipython will remind you of what the arguments are for that function.

.. code-block:: python

   >>> e = Experiment?
   Init signature: Experiment(self, expname, beamtime)
   Docstring:      <no docstring>
   File:           c:\users\billinge\documents\github\xpdacq\xpdacq\beamtime.py
   Type:           type

Here we see that Experiment takes 3 arguments (this will change in later versions of
the software, so always check!), ``self``, ``expname`` and ``beamtime``.
We can ignore ``self`` (it is just a reference of the object to itself) so
we just have to give two arguments, ``expname`` which we see is a string
with the name of the experiment and ``beamtime`` which is a beamtime object.

So let's go ahead and create it

.. code-block:: python

   >>> e = Experiment('InGaAsAlloyPD',bt)

and, just as before we can investigate it

.. code-block:: python

   >>> e.name
   'InGaAsAlloyPD'
   >>> e.type
   'ex'
   
so it is an object of type ``ex`` (experiment) with name ``'InGaAsAlloyPD'``
where the experiment is to study the phase diagram of an In1-xGaxAs alloy.

Let's take a look at its metadata store

.. code-block:: python

   >>> e.md
   {'bt_experimenters': {('Chia-Hao', 'Liu'), ('Simon', 'Billinge')},
   'bt_piLast': 'Billinge',
   'bt_safN': 300256,
   'bt_uid': '9b0c5878-cba4-11e5-8984-28b2bd4521c0',
   'bt_wavelength': 0.1818,
   'ex_name': 'InGaAsAlloyPD',
   'ex_uid': '4e45bf3e-cbc7-11e5-8b67-28b2bd4521c0

So it has a couple of experiment metadata items, 'ex_uid' (it created) 
and 'ex_name' (we gave it), but interestingly it carries with it all
the metadata from the beamtime object ``bt`` that we passed to it.

In general, at a beamtime, we may have two or more experiments that we 
want to accomplish during our time, in which case we would create a 
second Experiment instance, but give it the same ``bt`` metadata:

.. code-block:: python

   >>> e2 = Experiment('ProteinFolding',bt)
   >>> e2.md
   {'bt_experimenters': {('Chia-Hao', 'Liu'), ('Simon', 'Billinge')},
    'bt_piLast': 'Billinge',
    'bt_safN': 300256,
    'bt_uid': '9b0c5878-cba4-11e5-8984-28b2bd4521c0',
    'bt_wavelength': 0.1818,
    'ex_name': 'ProteinFolding',
    'ex_uid': 'c89120dc-cbc8-11e5-ac9b-28b2bd4521c0'}

Here, careful inspection will indicate that this experiment has a
different experiment-ID ``ex_uid`` and ``ex_name`` but all the beamtime
leve metadata are the same as the other experiment (because this experiment
is being done at the same beamtime!).

Finally, there will be a number of samples that are part of the same experiment.
For the InGaAs phase diagram study for example, we may have to make 5 samples:


.. code-block:: python

  >>> s1 = Sample('GaAs',e)
  >>> s2 = Sample('In0.25Ga0.75As',e)
  >>> s3 = Sample('InGaAs-5050',e)
  >>> s4 = Sample('IGA75-25',e)
  >>> s5 = Sample('InAs',e)
  >>> s1.md
  {'bt_experimenters': {('Chia-Hao', 'Liu'), ('Simon', 'Billinge')},
  'bt_piLast': 'Billinge',
  'bt_safN': 300256,
  'bt_uid': '9b0c5878-cba4-11e5-8984-28b2bd4521c0',
  'bt_wavelength': 0.1818,
  'ex_name': 'ProteinFolding',
  'ex_uid': 'c89120dc-cbc8-11e5-ac9b-28b2bd4521c0',
  'sa_name': 'InAs',
  'sa_uid': '415f8e06-cbca-11e5-92fe-28b2bd4521c0'}
  >>> s3.md
  {'bt_experimenters': {('Chia-Hao', 'Liu'), ('Simon', 'Billinge')},
  'bt_piLast': 'Billinge',
  'bt_safN': 300256,
  'bt_uid': '9b0c5878-cba4-11e5-8984-28b2bd4521c0',
  'bt_wavelength': 0.1818,
  'ex_name': 'ProteinFolding',
  'ex_uid': 'c89120dc-cbc8-11e5-ac9b-28b2bd4521c0',
  'sa_name': 'InAs',
  'sa_uid': '7c73f3a7-cbca-11e5-a0cb-28b2bd4521c0'} 

Hopefully you are getting the picture.  We will hand these sample
objects to the run engine when each scan or count is launched and
all the metadata will be associated with each scan, easily allowing
us to search, for example, for all the scans done on a sample as
part of this experiment.

At the time of writing, each object, such as Sample, is a container
for the barest minimum of metadata.  As time goes on we will increas
the number of things that you may save about samples and experiments.
Send us your requests!

return to :ref:`xpdu`
