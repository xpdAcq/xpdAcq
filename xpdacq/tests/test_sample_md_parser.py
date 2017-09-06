import pytest
from xpdacq.utils import excel_to_yaml


@pytest.mark.parametrize("input_dict, expect_rv",
                         [('TiO2:1, H2O:1, Ni:1', ({'H': 0.66, 'O': 0.99,
                                                    'Ti': 0.33, 'Ni': 0.33},
                                                   {'TiO2': 0.33,
                                                    'H2O': 0.33,
                                                    'Ni': 0.33},
                                                   'H0.66Ni0.33O0.99Ti0.33'))
                             , ('TiO2:, H2O:, Ni:1', ({'H': 0.66, 'O': 0.99,
                                                       'Ti': 0.33, 'Ni': 0.33},
                                                      {'TiO2': 0.33,
                                                       'H2O': 0.33,
                                                       'Ni': 0.33},
                                                      'H0.66Ni0.33O0.99Ti0.33')
                                )
                             , ('TiO2;, H2O:, Ni^1', ({'H': 0.66, 'O': 0.99,
                                                       'Ti': 0.33, 'Ni': 0.33},
                                                      {'TiO2': 0.33,
                                                       'H2O': 0.33,
                                                       'Ni': 0.33},
                                                      'H0.66Ni0.33O0.99Ti0.33')
                                )
                          ])
def test_phase_str_parser(input_dict, expect_rv):
    assert excel_to_yaml.phase_parser(input_dict) == expect_rv


def test_phase_str_parser_error():
    # edge case: not comma separated -> ValueError
    test_str = 'TiO2; H2O: Ni^1'
    with pytest.raises(ValueError):
        excel_to_yaml.phase_parser(test_str)


@pytest.mark.parametrize("input_str, expect_rv",
                         [('New Order, Joy Division, Smashing Pumpkins',
                           ['New Order', 'Joy Division',
                            'Smashing Pumpkins']),
                          ('New Order Joy Division Smashing Pumpkins  ',
                           ['New Order Joy Division Smashing Pumpkins'])])
def test_comma_separate_parser(input_str, expect_rv):
    assert excel_to_yaml._comma_separate_parser(input_str) == expect_rv


@pytest.mark.parametrize("input_str, expect_rv",
                         [('New Order, Joy Division, Smashing Pumpkins',
                           ['New', 'Order', 'Joy', 'Division',
                            'Smashing', 'Pumpkins']),
                          ('New Order Joy Division Smashing Pumpkins',
                           ['New Order Joy Division Smashing Pumpkins'])])
def test_name_parser(input_str, expect_rv):
    # name will go through two parsers, test both of them
    comma_sep_list = excel_to_yaml._comma_separate_parser(input_str)
    parsed_name = []
    for el in comma_sep_list:
        parsed_name.extend(excel_to_yaml._name_parser(el))
    assert parsed_name == expect_rv
