# go over collection functionalities

print('start beamtime ....')
bt = _start_beamtime('123')

print('bt list method ....')
bt.list()
print('define acquire objects...')
ex = Experiment('xpdAcq_test', bt)
sa = Sample('xpdAcq_test_Sample', ex)
print('define "ct" scanplan: exp = 0.5')
ct = ScanPlan('xpdAcq_test_ct','ct',{'exposure':0.5})
print('define "Tramp" scanplan: exp = 0.5, startingT = 300, endingT = 310, Tstep = 2')
TrampUp = ScanPlan('xpdAcq_test_Tramp','Tramp',{'exposure':0.5, 'startingT': 300, 'endingT': 310, 'Tstep':2})
TrampDown = ScanPlan('xpdAcq_test_Tramp','Tramp',{'exposure':0.5, 'startingT': 310, 'endingT': 300, 'Tstep':2})
print('define "time series" scanplan: exp = 0.5, num=10, delay = 2')
tseries = ScanPlan('xpdAcq_test_tseries', 'tseries', {'exposure':0.5, 'num':5, 'delay':2})

scan_list_up = [ct, TrampUp, tseries]
scan_list_down = [ct, TrampDown, tseries]

print('prun with different ScanPlans...')
for el in scan_list_up:
    prun(sa, el)
    save_last_tiff()

print('setupscan with different ScanPlans...')
for el in scan_list_down:
    setupscan(sa, el)
    save_last_tiff()

print('background with ct ScanPlans...')
setupscan(sa, ct)
save_last_tiff()

print('calibration with ct ScanPlans...')
calibration(sa, ct)
save_last_tiff()

print('dryrun with different ScanPlans...')
for el in scan_list_up:
    dryrun(sa, el)

print('=== end of collection functionalities test ===')
_end_beamtime()
