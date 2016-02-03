class XPDSTATE:
      def __init__(self, dirpath):
           self._cur_beamtime = {}
           self._cur_sample = {}
           self._cur_scan = {}
           self._cur_exposure = {}
           self._done_measurements = []

       def start_beamtime(self, pi_last, ):
           pass

       def change_sample(self, sample_details):
           pass

       def export_for_BS(self):
           out = dict()
           out.update(self._cur_beamtime)
           out.update(self._cur_exposure)

       def export_to_yaml(self):
           pass

       @classmethod
       def from_yaml(cls, fname):
           new_state = cls()
           with fopen(fname) as f:
               for k, v in yaml.read(f):
                   pass



   # in 99-settings.py

   try:
       STATE = XPDSTATE.from_yaml(some_fixed_path)
   except:
       STATE = XPDSTATE(some_fixed_path)


   def run_experiment1():
       md_dict = STATE.export_for_BS()

       ct_plan = Count(dets, n=3)
       def plan_gen():
           yield Msg()
           yield from ct_plan
           for t in temperature_ramp:
               yield Msg('set', temp_control, t, block_group='T')
               yield Msg('wait', None, block_group='T')
               yield from ct_plan

       gs.RE(plan_gen(), your_subs, **md_dict)



   def run_experiment2(*args, **kwargs):
       md_dict = STATE.export_for_BS()
       if not validate_md(md_dict):
           raise ValueError("blah blah")
       if get_key(*args, **kwargs) in STATE.done_we:
           res = input("are you sure you want to do this again?")
           if not res:
               return
       some_other_plan = AScanPlan(dets, motor, start, stop, step)

       res = chain(ct_plan, some_other_plan, ct_plan)
       gs.RE(res, your_subs, **md_dict)
