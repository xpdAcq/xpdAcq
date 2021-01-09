import bluesky.plans as bp

from xpdacq.xpdacq_conf import xpd_configuration


def test_sample_md_injection(fresh_xrun):
    """Test if the sample metadata is properly injected into the start."""
    xrun = fresh_xrun
    det = xpd_configuration["area_det"]
    sample_md = {"sample_name": "Ni", "sample_composition": {"Ni": 1.}}

    # callback to assert the sample metadata in start
    def assert_sample_md(name, doc):
        for key, value in sample_md.items():
            assert doc[key] == value

    xrun.subscribe(assert_sample_md, "start")
    xrun(sample_md, bp.count([det]))
