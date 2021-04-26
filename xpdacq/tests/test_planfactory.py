import pyFAI
from bluesky.simulators import summarize_plan
from pkg_resources import resource_filename

from xpdacq.planfactory import BasicPlans, MultiDistPlans


def test_BasicPlans(fake_devices, db, calib_data):
    xbp = BasicPlans(fake_devices.motor1, 0, 1, db)
    summarize_plan(xbp.count([fake_devices.det1], 2))
    summarize_plan(xbp.grid_scan([fake_devices.det1], fake_devices.motor2, 2, 3, 2))
    summarize_plan(xbp.config_by_poni(calib_data, resource_filename("xpdacq", "tests/Ni_poni_file.poni")))


def test_MultiDistPlans(fake_devices, calib_data, db):
    ai0 = pyFAI.AzimuthalIntegrator(dist=0)
    ai1 = pyFAI.AzimuthalIntegrator(dist=1)
    mdp = MultiDistPlans(fake_devices.motor1, 0, 1, db, fake_devices.motor2, calib_data, fake_devices.motor2)
    mdp.add_dist(0, "test0", ai0)
    mdp.add_dist(1, "test1", ai1)
    summarize_plan(mdp.count([fake_devices.det1], 2))
