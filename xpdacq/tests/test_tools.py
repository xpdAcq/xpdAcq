import pytest
import copy
from xpdacq.tools import clean_dict

@pytest.mark.parametrize("input_dict, output_dict",
                         [({'a': 1, 'b': 2, 'c': 3},
                           {'a': 1, 'b': 2,'c':3}),
                          ({'a.foo': 1, 'b.bar': 2, 'c': 3},
                           {'a,foo': 1, 'b,bar': 2, 'c': 3}),
                          ({'a.foo': {'b.bar': 2}, 'c': 3},
                           {'a,foo': {'b,bar': 2}, 'c': 3}),
                          ({'a.foo': {'b.bar': '2.foo'}, 'c': '3.bar'},
                           {'a,foo': {'b,bar': '2.foo'}, 'c': '3.bar'})
                         ])
def test_clean_dict(input_dict, output_dict):
    clean_dict(input_dict, '.', ',')  # modify dict in place
    assert input_dict == output_dict  # test equality
