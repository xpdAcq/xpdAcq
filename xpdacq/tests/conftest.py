import shutil
import sys
import uuid

import pytest
from databroker import Broker
from filestore.handlers import NpyHandler

from xpdan.tests.utils import insert_imgs
from xpdan.data_reduction import DataReduction
from xpdan.glbl import make_glbl
from xpdan.simulation import build_pymongo_backed_broker

if sys.version_info >= (3, 0):
    pass


@pytest.fixture(params=[
    # 'sqlite',
    'mongo'], scope='module')
def db(request):
    param_map = {
        # 'sqlite': build_sqlite_backed_broker,
        'mongo': build_pymongo_backed_broker}

    return param_map[request.param](request)


@pytest.fixture(scope='module')
def handler(exp_db):
    h = DataReduction(exp_db=exp_db)
    return h


@pytest.fixture(scope='module')
def exp_db(db):
    glbl = make_glbl(1)
    db2 = db
    mds = db2.mds
    fs = db2.fs
    insert_imgs(mds, fs, 5, (200, 200), glbl.base)
    yield db2
    print('removing {}'.format(glbl.base))
    shutil.rmtree(glbl.base)
    print("DROPPING DB")
    mds._connection.drop_database(mds.config['database'])
    print("DROPPING DB")
    fs._connection.drop_database(fs.config['database'])

