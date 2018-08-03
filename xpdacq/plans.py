from itertools import product
import numpy as np
import bluesky.preprocessors as bpp
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from xpdacq.xpdacq_conf import xpd_configuration

det = xpd_configuration['area_det']
shutter = xpd_configuration['shutter']
fb = xpd_configuration['filter_bank']
sh_open = xpd_configuration['open']
sh_close = xpd_configuration['close']
fb_attenuation = np.asarray([2, 4, 8, 16])


# Acq
def light_dark():
    """Plan to take a light then a dark and subtract the two for use in plans
    """
    # take dark
    yield from bps.abs_set(shutter, sh_close, wait=True)
    dark = yield from bps.trigger_and_read(det, name='dark')
    # take data
    yield from bps.abs_set(shutter, sh_open, wait=True)
    light = yield from bps.trigger_and_read(det)
    yield from bps.abs_set(shutter, sh_close, wait=True)
    data = light.astype(np.float32) - dark.astype(np.float32)
    return data


def tune_filters(upper_threshold=8000,
                 percentile=100 - .01,
                 lower_theshold=500):
    """Tune the filters to minimize the exposure time while not burning the
    detector.

    Parameters
    ----------
    upper_threshold : float
        Max number of counts for detector safety
    percentile : float
        Percentile to use to measure the max intensity (use percentile because
        of bad pixels)
    lower_theshold : float
        Threshold below which data is unreliable for measuring sample
        scattering power

    Returns
    -------
    plan : generator
        The plan:

    Notes
    -----
    This requires accurate attenuation factors for the filters.

    """
    # List of filter configurations in order of filter power
    # Need to set this since it could be non-unique
    filter_configurations = sorted(
        [np.asarray(x) for x in product([0, 1], repeat=4)],
        key=lambda x: np.prod((x * fb_attenuation)[np.nonzero(x)]),
        reverse=True
    )
    attenuations = np.asarray(
        [np.prod((x * fb_attenuation)[np.nonzero(x)]) for x in
         filter_configurations])

    @bpp.stage_decorator([det])
    @bpp.run_decorator()
    def inner():
        yield from bps.abs_set(det.cam.acquire_time, .1)
        for fc in filter_configurations:
            att = 1 / np.prod((fc * fb_attenuation)[np.nonzero(fc)])
            # set the filter banks
            for f, io in zip(fb, fc):
                yield from bps.abs_set(f, io, wait=True)
            data = yield from light_dark()

            # calculate the value of the top .01 percentile pixel
            v = np.percentile(data, percentile)

            # The value is too low to evaluate, bump to next configuration
            if v < lower_theshold:
                continue
        # compute the sample scattering power
        sp = v / att
        # compute filter config index to use
        fci = np.where((sp / attenuations) < upper_threshold)[0][-1]
        # set the bank
        for f, io in zip(fb, filter_configurations[fci]):
            yield from bps.abs_set(f, io, wait=True)

        # compute the exposure
        exposure = min(5, upper_threshold / (sp / attenuations[fci]))
        yield from bps.abs_set(det.cam.acquire_time, exposure)

    return (yield from inner())
