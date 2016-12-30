import pytest
from xpdacq.tools import regularize_dict_key, validate_dict_key

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


@pytest.mark.parametrize("input_dict",[{'a': 0.1}, {'a': '0.1'},
                                       {'a': {'foo': 0.1}},
                                       {'a': {'foo': '0.1.foo.bar'}},
                                       {0.1: 'a'}])
def test_validate_dict_key_success(input_dict):
    validate_dict_key(input_dict, '.', ',')


@pytest.mark.parametrize("input_dict",[{'a.': 0.1}, {'a.foo': 0.1},
                                       {'a.': {'foo': 0.1}},
                                       {'a': {'.foo': 0.1}},
                                       ])
def test_validate_dict_key_raise(input_dict):
    # fail cases
    with pytest.raises(RuntimeError):
        validate_dict_key(input_dict, '.', ',')
