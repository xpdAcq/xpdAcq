import os
import tempfile
import time
from uuid import uuid4

import numpy as np
from xpdsim.dets import nsls_ii_path
print(nsls_ii_path)

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
    dark_uid = str(uuid4())
    run_start = mds.insert_run_start(uid=str(uuid4()), time=time.time(),
                                     name='test-dark', dark_uid=dark_uid,
                                     mask='stuff',
                                     is_dark_img=True)
    data_keys = {
        'img': dict(source='testing', external='FILESTORE:',
                    dtype='array')}
    data_hdr = dict(run_start=run_start,
                    data_keys=data_keys,
                    time=time.time(), uid=str(uuid4()))
    descriptor = mds.insert_descriptor(**data_hdr)
    for i, img in enumerate([dark_img]):
        fs_uid = str(uuid4())
        fn = os.path.join(save_dir, fs_uid + '.npy')
        np.save(fn, img)
        # insert into FS
        fs_res = fs.insert_resource('npy', fn, resource_kwargs={})
        fs.insert_datum(fs_res, fs_uid, datum_kwargs={})
        mds.insert_event(
            descriptor=descriptor,
            uid=str(uuid4()),
            time=time.time(),
            data={'img': fs_uid},
            timestamps={},
            seq_num=i)
    mds.insert_run_stop(run_start=run_start,
                        uid=str(uuid4()),
                        time=time.time())
    imgs = [np.ones(shape)] * n
    run_start = mds.insert_run_start(uid=str(uuid4()), time=time.time(),
                                     name='test', dark_uid=dark_uid)
    data_keys = {
        'pe1_image': dict(source='testing', external='FILESTORE:',
                          dtype='array')}
    data_hdr = dict(run_start=run_start,
                    data_keys=data_keys,
                    time=time.time(), uid=str(uuid4()))
    descriptor = mds.insert_descriptor(**data_hdr)
    for i, img in enumerate(imgs):
        fs_uid = str(uuid4())
        fn = os.path.join(save_dir, fs_uid + '.npy')
        np.save(fn, img)
        # insert into FS
        fs_res = fs.insert_resource('npy', fn, resource_kwargs={})
        fs.insert_datum(fs_res, fs_uid, datum_kwargs={})
        mds.insert_event(
            descriptor=descriptor,
            uid=str(uuid4()),
            time=time.time(),
            data={'pe1_image': fs_uid},
            timestamps={'pe1_image': time.time()},
            seq_num=i)
    mds.insert_run_stop(run_start=run_start,
                        uid=str(uuid4()),
                        time=time.time())
    return save_dir
