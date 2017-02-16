#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Christopher J. Wright
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
import sys
import uuid
import time
import tempfile
import numpy as np
from time import strftime
from xpdsim.movers import cs700, shctl1
from xpdsim.dets import det_factory, nsls_ii_path, chess_path
import bluesky.examples as be


def build_pymongo_backed_broker():
    """Provide a function level scoped MDS instance talking to
    temporary database on localhost:27017 with v1 schema.

    """
    from databroker.broker import Broker
    from metadatastore.mds import MDS
    from filestore.utils import create_test_database
    from filestore.fs import FileStore
    from filestore.handlers import NpyHandler

    db_name = "mds_testing_disposable_{}".format(str(uuid.uuid4()))
    mds_test_conf = dict(database=db_name, host='localhost',
                         port=27017, timezone='US/Eastern')
    try:
       # nasty details: to save MacOS user
        mds = MDS(mds_test_conf, 1, auth=False)
    except TypeError:
        mds = MDS(mds_test_conf, 1)

    db_name = "fs_testing_base_disposable_{}".format(str(uuid.uuid4()))
    fs_test_conf = create_test_database(host='localhost',
                                        port=27017,
                                        version=1,
                                        db_template=db_name)
    fs = FileStore(fs_test_conf, version=1)
    fs.register_handler('npy', NpyHandler)

    db = Broker(mds, fs)
    #insert_imgs(db.mds, db.fs, 1, (20, 20))

    return db

# instantiate simulation objects
db = build_pymongo_backed_broker()
db.fs.register_handler('RWFS_NPY', be.ReaderWithFSHandler)
pe1c = det_factory('pe1c', db.fs, nsls_ii_path, shutter=shctl1,
                   save_path=tempfile.mkdtemp())
pe1c_chess = det_factory('pe1c_chess', db.fs, chess_path, shutter=shctl1,
                         save_path=tempfile.mkdtemp())


def insert_imgs(mds, fs, n, shape, save_dir=tempfile.mkdtemp()):
    """
    Insert images into mds and fs for testing

    Parameters
    ----------
    mds
    fs
    n
    shape
    save_dir

    Returns
    -------

    """
    # Insert the dark images
    dark_img = np.ones(shape)
    dark_uid = str(uuid.uuid4())
    run_start = mds.insert_run_start(uid=str(uuid.uuid4()), time=time.time(),
                                     name='test-dark', dark_uid=dark_uid,
                                     is_dark_img=True)
    data_keys = {
        'img': dict(source='testing', external='FILESTORE:',
                    dtype='array')}
    data_hdr = dict(run_start=run_start,
                    data_keys=data_keys,
                    time=time.time(), uid=str(uuid.uuid4()))
    descriptor = mds.insert_descriptor(**data_hdr)
    for i, img in enumerate([dark_img]):
        fs_uid = str(uuid.uuid4())
        fn = os.path.join(save_dir, fs_uid + '.npy')
        np.save(fn, img)
        # insert into FS
        fs_res = fs.insert_resource('npy', fn, resource_kwargs={})
        fs.insert_datum(fs_res, fs_uid, datum_kwargs={})
        mds.insert_event(
            descriptor=descriptor,
            uid=str(uuid.uuid4()),
            time=time.time(),
            data={'pe1_img': fs_uid},
            timestamps={},
            seq_num=i)
    mds.insert_run_stop(run_start=run_start,
                        uid=str(uuid.uuid4()),
                        time=time.time())
    imgs = [np.ones(shape)] * n
    run_start = mds.insert_run_start(uid=str(uuid.uuid4()), time=time.time(),
                                     name='test', dark_uid=dark_uid,
                                     sc_dk_field_uid=dark_uid)
    data_keys = {
        'pe1_image': dict(source='testing', external='FILESTORE:',
                          dtype='array')}
    data_hdr = dict(run_start=run_start,
                    data_keys=data_keys,
                    time=time.time(), uid=str(uuid.uuid4()))
    descriptor = mds.insert_descriptor(**data_hdr)
    exp_img = np.ones(shape)
    for i, light_img in enumerate([exp_img]):
        fs_uid = str(uuid.uuid4())
        fn = os.path.join(save_dir, fs_uid + '.npy')
        np.save(fn, light_img)
        # insert into FS
        fs_res = fs.insert_resource('npy', fn, resource_kwargs={})
        fs.insert_datum(fs_res, fs_uid, datum_kwargs={})
        mds.insert_event(
            descriptor=descriptor,
            uid=str(uuid.uuid4()),
            time=time.time(),
            data={'pe1_image': fs_uid},
            timestamps={'pe1_image': time.time()},
            seq_num=i)
    mds.insert_run_stop(run_start=run_start,
                        uid=str(uuid.uuid4()),
                        time=time.time())
    return save_dir
