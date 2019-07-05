# Helper functions
import time

def seconds_from_midnight():
    """

    :return: Number of seconds from midnight
    :rtype: int
    """
    t = time.gmtime()
    hour, minute, second = t[3], t[4], t[5]
    seconds_from_midnight = second + (minute + hour * 60) * 60
    return seconds_from_midnight


def mean_across_arrays(arrays):
    """
    Computes elementwise mean across arrays.
    E.g. for input [[1, 2, 4], [5, 3, 6]] returns [3, 2.5, 5]
    :param arrays: list of arrays of the same length
    :return: elementwise average across arrays
    """
    out_arr = []
    n_arrays = len(arrays)
    # Iterate through the elements in an array
    for i in range(len(arrays[0])):
        sm = 0
        # Iterate through all the arrays
        for array in arrays:
            sm += array[i]
        out_arr.append(sm/n_arrays)
    return out_arr
