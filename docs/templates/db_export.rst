Databroker Export
-----------------

Exporting a databroker is a good way to take your raw data home so it can be
analyzed after the fact.

The easy way
============
1. Mount your drive which you are going to store the data on
2. Create a folder on your drive for putting the portable databroker into
3. In a terminal start up ``bsui``
4. In a different terminal run ``portable_db_server <path/to/folder/on/mounted/drive``
5. Find all the headers you want copied (make sure that these headers include the darks and backgrounds, see below for more details)
6. In the ``bsui`` ipython session run 

.. code-block:: python

  import time
  for hdr in hdrs:
      for nd in hdr.documents():
          pub(*nd)
          # this is to make certain we don't overrun the server
          time.sleep(.1)

This will send data to the portable db server which will then write the associated files into the folder

7. Shut down the server once it is done copying files (use ``Ctrl+C``)
8. Unmount your drive

The hard way
============
1. Mount your drive which you are going to store the data on
2. Create a folder on your drive for putting the portable databroker into
3. In a terminal start up ``bsui``
4. Find all the headers you want copied (make sure that these headers include the darks and backgrounds, see below for more details)
5. In the ``bsui`` ipython session run

.. code-block:: python

    import io
    import os
    import yaml
    p = 'path/to/mounted/disk/folder'
    portable_template = """description: 'raw database'
        metadatastore:
            module: 'databroker.headersource.sqlite'
            class: 'MDS'
            config:
                directory: 'raw'
                timezone: 'US/Eastern'
        assets:
            module: 'databroker.assets.sqlite'
            class: 'Registry'
            config:
                dbpath: 'raw/assets.sqlite'
        handlers:
            NPY_SEQ:
                module: 'ophyd.sim'
                class: 'NumpySeqHandler'
        """
    with open(os.path.join(p, 'raw.yml'), 'w') as f:
        f.write(portable_template)
    pdb = Broker.from_config(yaml.unsafe_load(io.StringIO(portable_template)))
    # hdrs is the headers that you want to export
    db.export(hdrs, pdb, new_root=os.path.join(p, 'raw', 'data'))


7. Once finished unmount your drive

Finding the headers
===================
Make certain that you have all the headers you want otherwise you may need to
do this all over again.
Please see the `databroker documentation <https://blueskyproject.io/databroker/>`_ for general searching queries.
Here is an example

.. code-block:: python

    from xpdan.db_utils import query_background
    # search for a bunch of sample uids
    hdrs = []
    for uid in ['thing1', 'thing2']:
        hdrs += list(db(sa_uid=uid))

    # don't forget the backgrounds
    bg_hdrs = []
    for hdr in hdrs:
        bg_hdrs.extend(query_background(hdr.start, db))
    hdrs += bg_hdrs

    # and the darks
    hdrs += [db[hdr.start['sc_dk_field_uid']] for hdr in hdrs if 'sc_dk_field_uid' in hdr.start]
