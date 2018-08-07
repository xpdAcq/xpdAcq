from itertools import product
import numpy as np
import bluesky.preprocessors as bpp
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from xpdacq.xpdacq_conf import xpd_configuration

sh_open = xpd_configuration["open"]
sh_close = xpd_configuration["close"]
fb_attenuation = np.asarray([2, 4, 8, 16])


# Acq
def dark_light():
    """Plan to take a light then a dark and subtract the two for use in plans
    """
    # take dark
    yield from bps.abs_set(xpd_configuration["shutter"], sh_close, wait=True)
    dark = yield from bps.trigger_and_read(
        xpd_configuration["area_det"], name="dark"
    )
    # take data
    yield from bps.abs_set(xpd_configuration["shutter"], sh_open, wait=True)
    light = yield from bps.trigger_and_read(xpd_configuration["area_det"])
    yield from bps.abs_set(xpd_configuration["shutter"], sh_close, wait=True)
    data = light.astype(np.float32) - dark.astype(np.float32)
    return data


def tune_filters(
    upper_threshold=8000,
    percentile=100 - .01,
    lower_threshold=500,
    desired_exposure=.1,
):
    """Tune the filters to the desired exposure time while not burning the
    detector.

    Parameters
    ----------
    upper_threshold : float
        Max number of counts for detector safety
    percentile : float
        Percentile to use to measure the max intensity (use percentile because
        of bad pixels)
    lower_threshold : float
        Threshold below which data is unreliable for measuring sample
        scattering power
    desired_exposure : float
        The desired exposure. The exposure must be within the capabilities of
        the detector. This will also be used to sample the sample's scattering
        power.

    Returns
    -------
    plan : generator
        The plan

    Notes
    -----
    This requires accurate attenuation factors for the filters.

    """
    # List of filter configurations in order of filter power
    # TODO: Need to set this since it could be non-unique
    filter_configurations = sorted(
        [np.asarray(x) for x in product([0, 1], repeat=4)],
        key=lambda x: np.prod((x * fb_attenuation)[np.nonzero(x)]),
        reverse=True,
    )
    attenuations = 1 / np.asarray(
        [
            np.prod((x * fb_attenuation)[np.nonzero(x)])
            for x in filter_configurations
        ]
    )

    @bpp.stage_decorator([xpd_configuration["area_det"]])
    @bpp.run_decorator()
    def inner():
        yield from bps.abs_set(
            xpd_configuration["area_det"].cam.acquire_time, desired_exposure
        )
        for fc in filter_configurations:
            att = 1 / np.prod((fc * fb_attenuation)[np.nonzero(fc)])
            # set the filter banks
            yield from (
                bps.abs_set(f, io, wait=True)
                for f, io in zip(xpd_configuration["filter_bank"], fc)
            )
            data = yield from dark_light()

            # calculate the value of the top .01 percentile pixel
            v = np.percentile(data, percentile)

            # The value is too low to evaluate, bump to next configuration
            if v < lower_threshold:
                continue
            else:
                break
        # compute the sample scattering power
        sp = v / (att * desired_exposure)
        # compute filter config index to use
        fci = np.where(
            (sp * attenuations * desired_exposure) < upper_threshold
        )[0][-1]
        # set the bank
        yield from (
            bps.abs_set(f, io, wait=True)
            for f, io in zip(
                xpd_configuration["filter_bank"], filter_configurations[fci]
            )
        )

        # compute the exposure
        computed_exposure = upper_threshold / (sp * attenuations[fci])
        print("Extrapolated exposure: {}".format(computed_exposure))
        exposure = min(5, computed_exposure)
        print("Using exposure: {}".format(computed_exposure))
        expected_counts = sp * attenuations[fci] * exposure
        print("Expected counts: {}".format(expected_counts))
        yield from bps.abs_set(
            xpd_configuration["area_det"].cam.acquire_time, exposure
        )

    return (yield from inner())
