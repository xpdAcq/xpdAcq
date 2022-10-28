import typing as T
from dataclasses import dataclass
from functools import partial
import itertools as its

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import numpy as np
from bluesky.utils import Msg
from ophyd import Device, Signal

Plan = T.Generator[Msg, T.Any, T.Any]
Motor = T.Union[Device, Signal]
Number = T.Union[float, int]
Detector = Device
OtherDetectors = T.List[Detector]
Metadata = T.Optional[T.Dict[str, T.Any]]


def _take_reading(
    dets: OtherDetectors,
    static: Detector,
    moving: Detector,
    motor: Motor,
    pos_in: Number,
    pos_out: Number,
) -> Plan:
    return bpp.pchain(
        bps.mv(motor, pos_out),
        bp.count(dets + [static, motor]),
        bps.mv(motor, pos_in),
        bp.count(dets + [moving, motor]),
    )


@dataclass
class TwoDetectors:
    """Helper to compose two-detector plans.

    Attributes
    ----------
    static: Detector
        Detector not moving.
    moving: Detector
        Detector moving in and out of beam.
    motor: Motor
        Axis motor of the moving detector stage.
    pos_in: Number
        Position that moving detector is in the beam.
    pos_out: Number
        Position that moving detector is out of the beam.
    """

    static: Detector
    moving: Detector
    motor: Motor
    pos_in: Number
    pos_out: Number

    def take_reading(self, dets: OtherDetectors) -> Plan:
        """Take a reading of two detectors.

        It contains two bluesky runs. First, count the static dectector after the moving detector moves out. Second, count the moving detector after the detector moves in. It will count `dets` together with the moving or static detector and the moving motor. Please do not add moving, static detector or the moving motor in the `dets`.

        Parameters
        ----------
        dets : OtherDetectors
            Other detector to take a reading.
        """
        return _take_reading(
            dets, self.static, self.moving, self.motor, self.pos_in, self.pos_out
        )

    def _one_shot(self, detectors: OtherDetectors) -> Plan:
        return bps.one_shot(detectors, take_reading=self.take_reading)

    def _one_nd_scan(
        self,
        detectors: OtherDetectors,
        step: T.Dict[Motor, Number],
        pos_cahce: T.Dict[Motor, T.Optional[Number]],
    ) -> Plan:
        return bps.one_nd_step(
            detectors, step, pos_cahce, take_reading=self.take_reading
        )

    def _outer_scan(
        self,
        detectors: OtherDetectors,
        motors: T.List[Motor],
        lists: T.List[T.Sequence[Number]],
    ) -> Plan:
        m = len(motors)
        pos_cache = dict(zip(motors, [None] * m))
        for positions in its.product(*lists):
            step = dict(zip(motors, positions))
            yield from self._one_nd_scan(detectors, step, pos_cache)
        return

    def count(
        self, detectors: OtherDetectors, num: int = 1, delay: Number = None
    ) -> Plan:
        """Take one or more readings from detectors.

        Parameters
        ----------
        detectors : OtherDetectors
            list of 'readable' objects
        num : integer, optional
            number of readings to take; default is 1

            If None, capture data until canceled
        delay : iterable or scalar, optional
            Time delay in seconds between successive readings; default is 0.

        Notes
        -----
        If ``delay`` is an iterable, it must have at least ``num - 1`` entries or
        the plan will raise a ``ValueError`` during iteration.
        """
        return bps.repeat(partial(self._one_shot, detectors), num, delay)

    def list_grid_scan(self, detectors: OtherDetectors, *args) -> Plan:
        """Scan over a mesh; each motor is on an independent trajectory.

        Parameters
        ----------
        detectors: OtherDetectors
            list of 'readable' objects
        args: list
            patterned like (``motor1, position_list1,``
                            ``motor2, position_list2,``
                            ``motor3, position_list3,``
                            ``...,``
                            ``motorN, position_listN``)

            The first motor is the "slowest", the outer loop. ``position_list``'s
            are lists of positions, all lists must have the same length. Motors
            can be any 'settable' object (motor, temp controller, etc.).
        """
        motors = args[0::2]
        positions = args[1::2]
        return self._outer_scan(detectors, motors, positions)

    def grid_scan(self, detectors: OtherDetectors, *args) -> Plan:
        """Scan over a mesh; each motor is on an independent trajectory.

        Parameters
        ----------
        detectors: OtherDetectors
            list of 'readable' objects
        ``*args``
            patterned like (``motor1, start1, stop1, num1,``
                            ``motor2, start2, stop2, num2,``
                            ``motor3, start3, stop3, num3,`` ...
                            ``motorN, startN, stopN, numN``)

            The first motor is the "slowest", the outer loop. For all motors
            except the first motor, there is a "snake" argument: a boolean
            indicating whether to following snake-like, winding trajectory or a
            simple left-to-right trajectory.
        """
        motors = args[0::4]
        starts = args[1::4]
        stops = args[2::4]
        nums = args[3::4]
        positions = [
            np.linspace(start, stop, num)
            for start, stop, num in zip(starts, stops, nums)
        ]
        return self._outer_scan(detectors, motors, positions)
