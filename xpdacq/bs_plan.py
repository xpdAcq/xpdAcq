import os
import yaml
from bluesky.plans import  scan, Plan
from bluesky import RunEngine
from bluesky.callbacks import LiveTable
from bluesky.examples import det as pe1c, motor as cs700
from xpdacq.glbl import glbl

RE = RunEngine({})
RE.subscribe('all', LiveTable([pe1c, cs700]))

# base class for every customize plan
class YamlPlan(Plan):
    def to_yaml(self, yml_name):
        state = {attr: getattr(self, attr) for attr in self._fields}
        f_name = os.path.join(glbl.yaml_dir, yml_name)+'.yml'
        with open(f_name, 'w') as fout:
            yaml.dump(self, fout)
        #yaml.dump(state, open(fp, 'w'))


def temperature_scan(start, stop, num, *, md=None):
    yield from scan([pe1c], cs700, start, stop, num, md=md)


class TemperatureScan(YamlPlan):
    "This is a Plan or, if you set the 'md' attribute, it is a ScanPlan."
    _fields = ['start', 'stop', 'num']

    def __init__(self, start, stop, num):
        self.start = start
        self.stop = stop
        self.num = num

        _params = [str(start), str(stop), str(num)]
        __doc__ = temperature_scan.__doc__  # copies docstring from generator
        f_name = 'Tramp'
        f_name += '_'.join(_params)

        self.to_yaml(f_name)

    def _gen(self):
        yield from temperature_scan(self.start, self.stop, self.num,
                                    md=self.md)
def bs_prun(plan, sample):
    plan.md = sample
    RE(plan)
