from xpdacq.tools import clean_dict

def test_clean_dict():
    # case 1: oridinary dict, no changes
    test = {'a': 1, 'b': 2, 'c': 3}
    clean_dict(test, '.', ',')
    assert test == {'a': 1, 'b': 2, 'c': 3}
    # case 2: flat dict with target character
    test = {'a.foo': 1, 'b.bar': 2, 'c': 3}
    clean_dict(test, '.', ',')
    assert test == {'a,foo': 1, 'b,bar': 2, 'c': 3}
    # case 3: nested dict with target character
    test = {'a.foo': {'b.bar': 2}, 'c': 3}
    clean_dict(test, '.', ',')
    assert test == {'a,foo': {'b,bar': 2}, 'c': 3}
    # case 4: nested dict with target character, both key and val
    test = {'a.foo': {'b.bar': '2.foo'}, 'c': '3.bar'}
    clean_dict(test, '.', ',')
    assert test == {'a,foo': {'b,bar': '2.foo'}, 'c': '3.bar'}
