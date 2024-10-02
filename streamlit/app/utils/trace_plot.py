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

    fig = make_subplots(rows=len(stream_new), cols=1, shared_xaxes=True, vertical_spacing=0.001)
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
        if ((endtime - starttime) * sampling_rate < 10_000): #400_000
            __plot_straight(fig, tr, _i)
        else:
            __plot_min_max(fig, tr, _i, starttime)
        #fig.add_trace(curr_plot, row=_i + 1, col=1)
        
    # Set ticks.
    #self.__plot_set_x_ticks()
    #self.__plot_set_y_ticks()
    #xmin = self._time_to_xvalue(self.starttime)
    #xmax = self._time_to_xvalue(self.endtime)
    #ax.set_xlim(xmin, xmax)
    #self._draw_overlap_axvspan_legend()
    
    fig.update_xaxes(showline=True, linewidth=1, mirror=True, showgrid=True)
    fig.update_yaxes(showline=True, linewidth=1, mirror=True, showgrid=True)
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
        #x_values = ((trace.times() / SECONDS_PER_DAY) +
        #            date2num(trace.stats.starttime.datetime))
        # Tho: this below should be double checked
        x_values = np.array(trace.stats.starttime.ns + trace.times() * 1_000_000_000, dtype='datetime64[ns]')
        #x_values = np.array(trace.times(type="timestamp"), dtype='datetime64[s]')
        fig.add_scatter(x=x_values, y=trace.data, row=i + 1, col=1, showlegend=False)
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


def __plot_min_max(fig, trace, i, reftime):  # @UnusedVariable
    """
    Plots the data using a min/max approach that calculated the minimum and
    maximum values of each "pixel" and then plots only these values. Works
    much faster with large data sets.
    """
    #self._draw_overlap_axvspans(Stream(trace), ax)
    # Some variables to help calculate the values.
    # need dbl check below
    starttime = trace.starttime - reftime
    endtime = trace.endtime - reftime
    # The same trace will always have the same sampling_rate.
    sampling_rate = trace[0].stats.sampling_rate
    # width of x axis in seconds
    x_width = endtime - starttime
    # normal plots have x-axis in days, so convert x_width to seconds
    # number of samples that get represented by one min-max pair
    pixel_length = int(
        np.ceil((x_width * sampling_rate + 1) / self.width))
    # Loop over all the traces. Do not merge them as there are many samples
    # and therefore merging would be slow.
    for _i, tr in enumerate(trace):
        trace_length = len(tr.data)
        pixel_count = int(trace_length // pixel_length)
        remaining_samples = int(trace_length % pixel_length)
        remaining_seconds = remaining_samples / sampling_rate
        # Reference to new data array which does not copy data but can be
        # reshaped.
        if remaining_samples:
            data = tr.data[:-remaining_samples]
        else:
            data = tr.data
        data = data.reshape(pixel_count, pixel_length)
        min_ = data.min(axis=1) * tr.stats.calib
        max_ = data.max(axis=1) * tr.stats.calib
        # Calculate extreme_values and put them into new array.
        if remaining_samples:
            extreme_values = np.empty((pixel_count + 1, 2), dtype=float)
            extreme_values[:-1, 0] = min_
            extreme_values[:-1, 1] = max_
            extreme_values[-1, 0] = \
                tr.data[-remaining_samples:].min() * tr.stats.calib
            extreme_values[-1, 1] = \
                tr.data[-remaining_samples:].max() * tr.stats.calib
        else:
            extreme_values = np.empty((pixel_count, 2), dtype=float)
            extreme_values[:, 0] = min_
            extreme_values[:, 1] = max_
        # Finally plot the data.
        start = tr.stats.starttime - reftime
        end = tr.stats.endtime - reftime
        if remaining_samples:
            # the last minmax pair is inconsistent regarding x-spacing
            x_values = np.linspace(start, end - remaining_seconds,
                                    num=extreme_values.shape[0] - 1)
            x_values = np.concatenate([x_values, [end]])
        else:
            x_values = np.linspace(start, end, num=extreme_values.shape[0])
        x_values = np.repeat(x_values, 2)
        y_values = extreme_values.flatten()
        ax.plot(x_values, y_values, color=self.color)
    # remember xlim state and add callback to warn when zooming in
    #self._initial_xrange = (self._time_to_xvalue(self.endtime) -
    #                        self._time_to_xvalue(self.starttime))
    #self._minmax_plot_xrange_dangerous = False
    #ax.callbacks.connect("xlim_changed", self._warn_on_xaxis_zoom)
    # set label, write to self.ids
    #if hasattr(trace[0], 'label'):
    #    tr_id = trace[0].label
    #else:
    #    tr_id = trace[0].id
    #self.ids.append(tr_id)


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