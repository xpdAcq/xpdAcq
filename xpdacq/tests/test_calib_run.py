from xpdacq.calib import (_collect_img, xpdAcqException
                          _sample_name_phase_info_configuration)


@pytest.mark.parametrize('sample_name, phase_info, tag, exception',
                         [(None, None, 'calib', None),
                          (None, None, 'mask', None),
                          (None, 'Ni', 'calib', xpdAcqException),
                          ('Ni', None, 'calib',
                          ]
                         )
def test_bar(inp, exception):
        if exception is None:
            bar(inp)
        else:
            with pytest.raises(exception):
                bar(inp)


def test_collect_img(fresh_xrun, sample_name, phase_info, tag):
    xrun = fresh_xrun
    # case1. test calib
    sample_md = _sample_name_phase_info_configuration(sample_name,
                                                      phase_info, tag)
    img, fn_template = _collect_img(5, True, {}, 'mask', xrun)
    assert 1==1
