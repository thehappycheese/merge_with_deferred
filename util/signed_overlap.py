import numpy as np
from numpy import typing as npt

def overlap(a:npt.NDArray, b:npt.NDArray, x:npt.NDArray, y:npt.NDArray):
    """Compute the signed distance between lists of intervals"""
    overlap_min = np.maximum(a, x.reshape(-1,1))
    overlap_max = np.minimum(b, y.reshape(-1,1))
    signed_overlap_len = overlap_max - overlap_min
    return signed_overlap_len