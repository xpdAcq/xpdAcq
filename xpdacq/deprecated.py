def _cal_frames(total_time):
    ''' function to calculate number of frames to take

        Parameters
        ----------
        total_time : float
            - total time in seconds

        frame_rate : float
            - 'unit' of exposure

        Returns
        -------
        out_put : tuple
            - (integer, fractional number)

    '''
    import math
    total_float = total_time / expo_threshold
    parsed_num = math.modf(total_float)

    # number of frames that will collect with maximum exposure
    num_int = parsed_time[1]

    # last frame, collect fractio of exposure threshold
    num_dec = (parsed_time[0] * expo_threshold) / frame_rate

    return (num_int, num_dec)
