import pytest
from xpdacq.tools import regularize_dict_key

@pytest.mark.parametrize("input_dict, output_dict",
                         [({'a': 1, 'b': 2, 'c': 3},
                           {'a': 1, 'b': 2, 'c': 3}),
                          ({'a.foo': 1, 'b.bar': 2, 'c': 3},
                           {'a,foo': 1, 'b,bar': 2, 'c': 3}),
                          ({'a.foo': {'b.bar': 2}, 'c': 3},
                           {'a,foo': {'b,bar': 2}, 'c': 3}),
                          ({'a.foo': {'b.bar': '2.foo'}, 'c': '3.bar'},
                           {'a,foo': {'b,bar': '2.foo'}, 'c': '3.bar'}),
                          ({0.8:'foo', '0.8': 'bar'},
                           {0.8:'foo', '0,8': 'bar'}),
                          ({0.8:{'a.foo':'bar'}, '0.8': 'bar'},
                           {0.8:{'a,foo':'bar'}, '0,8': 'bar'})
                         ])
def test_regularize_dict_key(input_dict, output_dict):
    regularize_dict_key(input_dict, '.', ',')  # modify dict in place
    assert input_dict == output_dict  # test equality
