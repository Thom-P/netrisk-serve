from copy import copy

import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from obspy import Stream, Trace, UTCDateTime
from obspy.imaging.util import (_set_xaxis_obspy_dates, _id_key, _timestring)

from matplotlib.dates import date2num


MINMAX_ZOOMLEVEL_WARNING_TEXT = "Warning: Zooming into MinMax Plot!"
SECONDS_PER_DAY = 3600.0 * 24.0
DATELOCATOR_WARNING_MSG = (
    "AutoDateLocator was unable to pick an appropriate interval for this date "
    "range. It may be necessary to add an interval value to the "
    "AutoDateLocator's intervald dictionary.")



# adapt to plotly
# copied and modified from obspy
def plot_traces(traces):
    """
    Plot the Traces showing one graph per Trace.
    Plots the whole time series for self.max_npts points and less. For more
    points it plots minmax values.
    """
    stream_new = []
    # Generate sorted list of traces (no copy)
    # Sort order: id, starttime, endtime
    ids = __get_mergable_ids(traces)
    for id in ids:
        stream_new.append([])
        for tr in traces:
            tr_id = __get_merge_id(tr)
            if tr_id == id:
                # does not copy the elements of the data array
                tr_ref = copy(tr)
                if tr_ref.data.size:
                    stream_new[-1].append(tr_ref)
        # delete if empty list
        if not len(stream_new[-1]):
            stream_new.pop()
            continue
    # If everything is lost in the process raise an Exception.
    if not len(stream_new):
        raise Exception("Nothing to plot")
    
    starttime = min([trace.stats.starttime for trace in traces])
    endtime = max([trace.stats.endtime for trace in traces])

    fig = make_subplots(rows=len(stream_new), cols=1)
    # Create helper variable to track ids and min/max/mean values.
    ids = []
    # Loop over each Trace and call the appropriate plotting method.
    axis = []
    for _i, tr in enumerate(stream_new):
        # Each trace needs to have the same sampling rate.
        sampling_rates = {_tr.stats.sampling_rate for _tr in tr}
        if len(sampling_rates) > 1:
            msg = "All traces with the same id need to have the same " + \
                    "sampling rate."
            raise Exception(msg)
        sampling_rate = sampling_rates.pop()
        #if _i == 0:
        #    sharex = None
        #else:
        #    sharex = axis[0]
        #ax = self.fig.add_subplot(len(stream_new), 1, _i + 1,
        #                            sharex=sharex, **axis_facecolor_kwargs)



        #self.axis.append(ax)
        method = "full"
        if ((endtime - starttime) * sampling_rate > 400_000):
            method = "fast"
        #if method_ == 'full':
        __plot_straight(fig, tr, _i)
        #curr_plot = go.Scatter(x=[0, 1, 2], y=[0, 1, 2])
        #elif method_ == 'fast':
        #    curr_plot = __plot_min_max(stream_new[_i])
        #fig.add_trace(curr_plot, row=_i + 1, col=1)
        
    # Set ticks.
    #self.__plot_set_x_ticks()
    #self.__plot_set_y_ticks()
    #xmin = self._time_to_xvalue(self.starttime)
    #xmax = self._time_to_xvalue(self.endtime)
    #ax.set_xlim(xmin, xmax)
    #self._draw_overlap_axvspan_legend()
    return fig


def __plot_straight(fig, trace, i):  
        """
        Just plots the data samples in the self.stream. Useful for smaller
        datasets up to around 1000000 samples (depending on the machine on
        which it's being run).

        Slow and high memory consumption for large datasets.
        """
        # trace argument seems to actually be a list of traces..
        st = Stream(trace)
        #self._draw_overlap_axvspans(st, ax)
        for trace in st:
            # Check if it is a preview file and adjust accordingly.
            # XXX: Will look weird if the preview file is too small.
            if trace.stats.get('preview'):
                # Mask the gaps.
                trace.data = np.ma.masked_array(trace.data)
                trace.data[trace.data == -1] = np.ma.masked
                # Recreate the min_max scene.
                dtype = trace.data.dtype
                old_time_range = trace.stats.endtime - trace.stats.starttime
                data = np.empty(2 * trace.stats.npts, dtype=dtype)
                data[0::2] = trace.data / 2.0
                data[1::2] = -trace.data / 2.0
                trace.data = data
                # The times are not supposed to change.
                trace.stats.delta = (
                    old_time_range / float(trace.stats.npts - 1))
            trace.data = np.require(trace.data, np.float64) * trace.stats.calib
            # convert seconds of relative sample times to days and add
            # start time of trace.
            x_values = ((trace.times() / SECONDS_PER_DAY) +
                        date2num(trace.stats.starttime.datetime))
            fig.add_scatter(x=x_values, y=trace.data, row=i + 1, col=1)
        # Write to self.ids
        #trace = st[0]
        #if trace.stats.get('preview'):
        #    tr_id = trace.id + ' [preview]'
        #elif hasattr(trace, 'label'):
        #    tr_id = trace.label
        #else:
        #    tr_id = trace.id
        #self.ids.append(tr_id)
        return



def __get_mergable_ids(traces):
    ids = set()
    for tr in traces:
        ids.add(__get_merge_id(tr))
    return sorted(ids, key=_id_key)

def __get_merge_id(tr):
    tr_id = tr.id
    # don't merge normal traces with previews
    try:
        if tr.stats.preview:
            tr_id += 'preview'
    except AttributeError:
        pass
    # don't merge traces with different processing steps
    try:
        if tr.stats.processing:
            tr_id += str(tr.stats.processing)
    except AttributeError:
        pass
    return tr_id