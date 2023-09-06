import adaptivekde as ad
import numpy as np
from scipy.signal import argrelextrema
from KDEpy import FFTKDE

def time_to_fraction_of_day(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds / 86400  # 86400 seconds in a day

def assign_clusters(data, t, mi):
    # Assign clusters based on minima thresholds
    cluster_assignments = np.zeros_like(data, dtype=int)
    for i, thresh in enumerate(mi):
        mask = ((data >= t[thresh]) & 
                (data < (t[mi[i+1]] if i+1 < len(mi) else float('inf'))))
        cluster_assignments[mask] = i + 1
    # Handle data points before the first minimum
    cluster_assignments[data < t[mi[0]]] = 0
    return cluster_assignments

def adaptive(data, method='adaptivekde', bw='ISJ', kernel='gaussian'):
    data = np.asarray(data)
    if method == 'adaptivekde':
        # Use the ssvkernel function to get the kernel density estimate
        repeated = np.repeat(data, 10)
        y, t, _, _, _, _, _ = ad.ssvkernel(repeated)
    else:
        t, y = FFTKDE(bw=bw, kernel=kernel).fit(data).evaluate()
    # Identify local minima and maxima
    mi, _ = argrelextrema(y, np.less)[0], argrelextrema(y, np.greater)[0]
    # Assign clusters
    cluster_assignments = assign_clusters(data, t, mi)
    return cluster_assignments
