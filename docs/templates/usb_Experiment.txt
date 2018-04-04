.. _usb_experiment:

Setting up your XPD acuisition objects
--------------------------------------

Overview
""""""""

The basic workflow is

 #. Set up xpdAcq ``Sample`` objects. These contain information about the samples and experimental conditions.
 #. Set up xpdAcq ``ScanPlan`` objects.  These contain information used to run the scan, and metadata about the scan.
 #. Run scans by passing one ``Sample`` and one ``ScanPlan`` object to the run engine ``xrun``. Data will be measured and saved to the NSLS-II file-store with all the metadata in the objects saved with it.
 #. Extract scans and data that you want from the data-store by searching on the metadata, selecting the data you want and extracting it in the form you want it (e.g., tiff files)
 #. Analyze the data, by integrating images to 1D diffraction patterns, F(Q), and PDFs, subtracting backgrounds, plotting and fitting models
 #. Export all the data, both raw tiffs and analyzed data, that you want.

Note that the raw data, and metadata, will be stored indefinitely by NSLS-II, and can be searched for and extracted at any time in the future.

Hierarchy of Sample objects
""""""""""""""""""""""""""""""""""""""

The goal of the ``xpdAcq`` is to save data with as much accurate metadata
as possible with as little user-typing as possible.  To do this we associate
metadata with appropriate levels of the beamtime hierarchy laid out in :ref:`sb_icollection`.
In :ref:`usb_beamtime` we discussed setting up the main ``Beamtime`` object.  Here we set
up the an object at the next level down in hierarchy, ``Sample``.

The basic syntax is ``sa = Sample(arg1, arg2,...)``, where the ``args`` are the arguments
or parameters of the object, but it is always helpful to have a little reminder
of what are the required and optional arguments of this object.  ``ipython`` offers a
handy feature that you can type a ``?`` instead of the parentheses after a function and
ipython will remind you of what the arguments are for that function.

.. code-block:: python

  >>> sa = Sample?
  Init signature: Sample(beamtime, sample_md, **kwargs)
  Docstring:
  class that carries sample-related metadata

  after creation, this Sample object will be related to Beamtime
  object given as argument and will be available in bt.list()

  Parameters
  ----------
  beamtime : xpdacq.beamtime.Beamtime
   object representing current beamtime
  sample_md : dict
   dictionary contains all sample related metadata
  kwargs :
   keyword arguments for extr metadata

  Examples
  --------
  >>> Sample(bt, {'sample_name': 'Ni', 'sample_composition':{'Ni': 1}})

  >>> Sample(bt, {'sample_name': 'TiO2',
               'sample_composition':{'Ti': 1, 'O': 2}})

  Please refer to http://xpdacq.github.io for more examples.
  Init docstring:
  Initialize a ChainMap by setting *maps* to the given mappings.
  If no mappings are provided, a single empty dictionary is used.

Here we see that ``Sample`` takes 3 arguments (this will change in later versions of
the software, so always check!), ``beamtime``, ``sample_md`` and ``**kwargs``.
``beamtime`` which is a beamtime object,``sample_md`` is a dictionary and ``kwargs`` is
a standard python argument. See reference `here <https://docs.python.org/3.5/faq/programming.html>`_.

We also see there are examples on how to create a valid ``Sample`` object, so let's go ahead and create it

.. code-block:: python

   >>> sa = Sample(bt, {'sample_name': 'Ni', 'sample_composition':{'Ni': 1}})

and, just as before we can investigate it

.. code-block:: python

  >>> type(sa)
  xpdacq.beamtime.Sample

so it is an object of type ``xpdacq.beamtime.Sample``.

Let's take a look at its metadata store

.. code-block:: python

  >>> sa.md
  {'bt_experimenters': ['Tim', 'Liu'],
  'bt_piLast': 'Billinge',
  'bt_safN': '300564',
  'bt_uid': 'fbb381c3',
  'bt_wavelength': 0.1832,
  'sa_uid': 'f3323ad0',
  'sample_composition': {'Ni': 1},
  'sample_name': 'Ni'}

So it has a couple of experiment metadata items, 'sa_uid' (it created)
and 'sample_name' (we gave it), but interestingly it carries with it all
the metadata from the beamtime object ``bt`` that we passed to it.


For the InGaAs phase diagram study for example,we may have to make 5 samples:

.. code-block:: python

  >>> s1 = Sample(bt, {'sample_name':'GaAs', 'sample_composition':{'Ga':1., 'As':1.}})
  >>> s2 = Sample(bt, {'sample_name':'In0.25Ga0.75As', 'sample_composition':{'In':0.25, 'Ga':0.75, 'As':1.}})
  >>> s3 = Sample(bt, {'sample_name':'In0.5Ga0.5As', 'sample_composition':{'In':0.5, 'Ga':0.5, 'As':1.}})
  >>> s4 = Sample(bt, {'sample_name':'In0.75Ga0.25As', 'sample_composition':{'In':0.75, 'Ga':0.25, 'As':1.}})
  >>> s5 = Sample(bt, {'sample_name':'InAs', 'sample_composition':{'In':1., 'As':1.}})

  >>> s1.md
  {'bt_experimenters': ['Tim', 'Liu'],
  'bt_piLast': 'Billinge',
  'bt_safN': '300564',
  'bt_uid': 'fbb381c3',
  'bt_wavelength': 0.1832,
  'sa_uid': '4557b649',
  'sample_composition': {'As': 1.0, 'Ga': 1.0},
  'sample_name': 'GaAs'}

  >>> s3.md
  {'bt_experimenters': ['Tim', 'Liu'],
  'bt_piLast': 'Billinge',
  'bt_safN': '300564',
  'bt_uid': 'fbb381c3',
  'bt_wavelength': 0.1832,
  'sa_uid': '3bac77a8',
  'sample_composition': {'As': 1.0, 'Ga': 0.5, 'In': 0.5},
  'sample_name': 'In0.5Ga0.5As'}

Here, careful inspection will indicate that among various ``Sample`` objects,
there are different sample-ID ``sa_uid`` and ``sample_name`` but all the ``beamtime``
leve metadata are the same as the other samples (because this series of samples
is being done at the same beamtime!).

Hopefully you are getting the picture.  We will hand these sample
objects to the run engine when each scan is launched and
all the metadata up the stack will be associated with each scan, easily allowing
us to search, for example, for "all the scans done on sample ``'InGas'`` as
part of this beamtime".

Other metadata is saved such as date-time at the time of running, so we could
search for "the scan that was running at 5pm on Friday".  We also differentiate
production runs and setup scans.  By default the search will not return the
setup scans, though they can be retrieved if and when needed.  You can also
store any other metadata that you want at each level so you can tag data
and search in a very powerful way.  The search capabilities in the xpdAcq suite
are still under development, so please share your requests (sb2896@columbia.edu).

At the time of writing, each object, such as Sample, is a container
for the barest minimum of metadata.  As time goes on we will increase
the number of things that you may save about samples and experiments.
Send us your requests here too (sb2896@columbia.edu)!
