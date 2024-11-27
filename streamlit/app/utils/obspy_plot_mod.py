# Copied from Obspy and modified by tplanes to use plotly instead of matplotlib
# and allow enhanced plot interactivity in streamlit


# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Filename: waveform.py
#  Purpose: Waveform plotting for obspy.Stream objects
#   Author: Lion Krischer
#    Email: krischer@geophysik.uni-muenchen.de
#
# Copyright (C) 2008-2012 Lion Krischer
# --------------------------------------------------------------------
"""
Waveform plotting for obspy.Stream objects.

:copyright:
    The ObsPy Development Team (devs@obspy.org)
:license:
    GNU Lesser General Public License, Version 3
    (https://www.gnu.org/copyleft/lesser.html)
"""
import os
from copy import copy

import numpy as np
import plotly.graph_objects as go
from obspy import Stream, Trace
from obspy.geodetics import kilometer2degrees
from obspy.imaging.util import _id_key
from matplotlib.dates import date2num
from plotly.subplots import make_subplots

MINMAX_ZOOMLEVEL_WARNING_TEXT = "Warning: Zooming into MinMax Plot!"
SECONDS_PER_DAY = 3600.0 * 24.0
DATELOCATOR_WARNING_MSG = (
    "AutoDateLocator was unable to pick an appropriate interval for this date "
    "range. It may be necessary to add an interval value to the "
    "AutoDateLocator's intervald dictionary.")


class ModifiedWaveformPlotting(object):
    """
    Class that provides several solutions for plotting large and small waveform
    data sets.

    .. warning::

        This class should NOT be used directly, instead use the
        :meth:`~obspy.core.stream.Stream.plot` method of the
        ObsPy :class:`~obspy.core.stream.Stream` or
        :class:`~obspy.core.trace.Trace` objects.

    It uses matplotlib to plot the waveforms.
    """

    def __init__(self, **kwargs):
        """
        Checks some variables and maps the kwargs to class variables.
        """
        self.kwargs = kwargs
        self.stream = kwargs.get('stream')
        # Check if it is a Stream or a Trace object.
        if isinstance(self.stream, Trace):
            self.stream = Stream([self.stream])
        elif not isinstance(self.stream, Stream):
            msg = 'Plotting is only supported for Stream or Trace objects.'
            raise TypeError(msg)
        # Stream object should contain at least one Trace
        if len(self.stream) < 1:
            msg = "Empty stream object"
            raise IndexError(msg)
        self.stream = self.stream.copy()
        # Type of the plot.
        self.type = kwargs.get('type', 'normal')
        # Start and end times of the plots.
        self.starttime = kwargs.get('starttime', None)
        self.endtime = kwargs.get('endtime', None)
        self.fig_obj = kwargs.get('fig', None)
        # If no times are given take the min/max values from the stream object.
        if not self.starttime:
            self.starttime = min([trace.stats.starttime for trace in
                                  self.stream])
        if not self.endtime:
            self.endtime = max([trace.stats.endtime for trace in self.stream])
        self.stream.trim(self.starttime, self.endtime)
        # Assigning values for type 'section'
        self.sect_offset_min = kwargs.get('offset_min', None)
        self.sect_offset_max = kwargs.get('offset_max', None)
        self.sect_dist_degree = kwargs.get('dist_degree', False)
        # TODO Event data from class Event()
        self.ev_coord = kwargs.get('ev_coord', None)
        self.alpha = kwargs.get('alpha', 0.5)
        self.sect_plot_dx = kwargs.get('plot_dx', None)
        if self.sect_plot_dx is not None and not self.sect_dist_degree:
            self.sect_plot_dx /= 1e3
        self.sect_timedown = kwargs.get('time_down', False)
        self.sect_recordstart = kwargs.get('recordstart', None)
        self.sect_recordlength = kwargs.get('recordlength', None)
        self.sect_norm_method = kwargs.get('norm_method', 'trace')
        self.sect_user_scale = kwargs.get('scale', 1.0)
        self.sect_vred = kwargs.get('vred', None)
        if self.sect_vred and self.sect_dist_degree:
            self.sect_vred = kilometer2degrees(self.sect_vred / 1e3)
        self.sect_orientation = kwargs.get('orientation', 'vertical')
        if self.type == 'relative':
            self.reftime = kwargs.get('reftime', self.starttime)
        elif self.type == 'section':
            self.sect_reftime = kwargs.get('reftime', None)
        # Whether to use straight plotting or the fast minmax method. If not
        # set explicitly by the user "full" method will be used by default and
        # "fast" method will be used above some threshold of data points to
        # plot.
        self.plotting_method = kwargs.get('method', None)
        # Below that value the data points will be plotted normally. Above it
        # the data will be plotted using a different approach (details see
        # below). Can be overwritten by the above self.plotting_method kwarg.
        if self.type == 'section':
            # section may consists of hundreds of seismograms
            self.max_npts = 10000
        else:
            self.max_npts = 400000
        # If automerge is enabled, merge traces with the same id for the plot.
        self.automerge = kwargs.get('automerge', True)
        # If equal_scale is enabled, all plots are equally scaled.
        self.equal_scale = kwargs.get('equal_scale', True)
        # Set default values.
        # The default value for the size is determined dynamically because
        # there might be more than one channel to plot.
        self.size = kwargs.get('size', None)
        # Values that will be used to calculate the size of the plot.
        self.default_width = 800
        self.default_height_per_channel = 250
        if not self.size:
            self.width = 800
            # Check the kind of plot.
            if self.type == 'dayplot':
                self.height = 600
            elif self.type == 'section':
                self.width = 1000
                self.height = 600
            else:
                # One plot for each trace.
                if self.automerge:
                    count = self.__get_mergable_ids()
                    count = len(count)
                else:
                    count = len(self.stream)
                self.height = count * 250
        else:
            self.width, self.height = self.size
        # Interval length in minutes for dayplot.
        self.interval = 60 * kwargs.get('interval', 15)
        # Scaling.
        self.vertical_scaling_range = kwargs.get('vertical_scaling_range',
                                                 None)
        # Dots per inch of the plot. Might be useful for printing plots.
        self.dpi = kwargs.get('dpi', 100)
        # Color of the graph.
        if self.type == 'dayplot':
            self.color = kwargs.get('color', ('#B2000F', '#004C12', '#847200',
                                              '#0E01FF'))
            if isinstance(self.color, str):
                self.color = (self.color,)
            self.number_of_ticks = kwargs.get('number_of_ticks', None)
        else:
            self.color = kwargs.get('color', 'k')
            self.number_of_ticks = kwargs.get('number_of_ticks', 4)
        # Background, face and grid color.
        self.background_color = kwargs.get('bgcolor', 'w')
        self.face_color = kwargs.get('face_color', 'w')
        self.grid_color = kwargs.get('grid_color', 'black')
        self.grid_linewidth = kwargs.get('grid_linewidth', 0.5)
        self.grid_linestyle = kwargs.get('grid_linestyle', ':')
        # Transparency. Overwrites background and facecolor settings.
        self.transparent = kwargs.get('transparent', False)
        if self.transparent:
            self.background_color = None
        # Ticks.
        if self.type == 'relative':
            self.tick_format = kwargs.get('tick_format', '%.2f')
        else:
            self.tick_format = kwargs.get('tick_format', '%H:%M:%S')
        self.tick_rotation = kwargs.get('tick_rotation', 0)
        # Whether or not to save a file.
        self.outfile = kwargs.get('outfile')
        self.handle = kwargs.get('handle')
        # File format of the resulting file. Usually defaults to PNG but might
        # be dependent on your matplotlib backend.
        self.format = kwargs.get('format')
        self.show = kwargs.get('show', True)
        self.draw = kwargs.get('draw', True)
        self.block = kwargs.get('block', True)
        # plot parameters options
        self.x_labels_size = kwargs.get('x_labels_size', 8)
        self.y_labels_size = kwargs.get('y_labels_size', 8)
        self.title_size = kwargs.get('title_size', 10)
        self.linewidth = kwargs.get('linewidth', 1)
        self.linestyle = kwargs.get('linestyle', '-')
        self.subplots_adjust_left = kwargs.get('subplots_adjust_left', 0.12)
        self.subplots_adjust_right = kwargs.get('subplots_adjust_right', 0.88)
        self.subplots_adjust_top = kwargs.get('subplots_adjust_top', 0.95)
        self.subplots_adjust_bottom = kwargs.get('subplots_adjust_bottom', 0.1)
        self.right_vertical_labels = kwargs.get('right_vertical_labels', False)
        self.one_tick_per_line = kwargs.get('one_tick_per_line', False)
        self.show_y_UTC_label = kwargs.get('show_y_UTC_label', True)
        # self.title = kwargs.get('title', self.stream[0].id)
        # to silence warning
        self.title = kwargs.get('title', self.stream.traces[0].id)
        self.fillcolor_pos, self.fillcolor_neg = \
            kwargs.get('fillcolors', (None, None))

    def __del__(self):
        """
        Destructor closes the figure instance if it has been created by the
        class.
        """
        # this garbage collector quick n dirty fix causes things like st.plot()
        # in plot directive code for images in the docs to not appear anymore,
        # because apparently newer sphinx looks for still active Figure objects
        # *after* running the code and ignores figures that get shown *during*
        # running the code, so for now add more magic that prevents garbage
        # collection of figures here, when in CI (detected by env variable set
        # by github actions) see #3036
        if os.environ.get('CI') == 'true':
            return
        import matplotlib.pyplot as plt
        if self.kwargs.get('fig', None) is None and \
                not self.kwargs.get('handle'):
            plt.close()

    def __get_merge_id(self, tr):
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

    def __get_mergable_ids(self):
        ids = set()
        if self.stream:
            for tr in self.stream:
                ids.add(self.__get_merge_id(tr))
        return sorted(ids, key=_id_key)

    def plot_waveform(self, *args, **kwargs):
        """
        Creates a graph of any given ObsPy Stream object. It either saves the
        image directly to the file system or returns a binary image string.

        For all color values you can use legit HTML names, HTML hex strings
        (e.g. '#eeefff') or you can pass an RGB tuple, where each of R, G, and
        B are in the range [0, 1]. You can also use single letters for basic
        built-in colors ('b' = blue, 'g' = green, 'r' = red, 'c' = cyan,
        'm' = magenta, 'y' = yellow, 'k' = black, 'w' = white) and gray shades
        can be given as a string encoding a float in the 0-1 range.
        """
        # import matplotlib.pyplot as plt
        # Setup the figure if not passed explicitly.
        if not self.fig_obj:
            self.__setup_figure()
        else:
            self.fig = self.fig_obj
        # Determine kind of plot and do the actual plotting.
        if self.type == 'dayplot':
            return  # not yet implemented with plotly
            # self.plot_day(*args, **kwargs)
        elif self.type == 'section':
            return  # not yet implemented with plotly
            # self.plot_section(*args, **kwargs)
        else:
            self.plot(*args, **kwargs)
        # Adjust the subplot so there is always a fixed margin on every side
        # if self.type != 'dayplot':
        #    fract_y = 60.0 / self.height
        #    fract_y2 = 40.0 / self.height
        #    fract_x = 80.0 / self.width
        #    self.fig.subplots_adjust(top=1.0 - fract_y, bottom=fract_y2,
        #                             left=fract_x, right=1.0 - fract_x / 2)
        # if self.type == 'section':
        #    self.fig.subplots_adjust(bottom=0.12)

        self.fig.update_xaxes(showline=True, linewidth=1, showgrid=True)
        self.fig.update_xaxes(mirror=True, row=1, col=1)
        self.fig.update_xaxes(title_text='Time', row=len(self.axis), col=1)
        self.fig.update_yaxes(showline=True, linewidth=1, mirror=True,
                              showgrid=True)

        # amplitude units fetched in caling script
        # self.fig.add_annotation(text="Amplitude ({y_units})", textangle=-90,
        # xref='paper', xanchor='right', xshift=-90, x=0, yref='paper', y=0.5,
        # showarrow=False)

        return self.fig

    def plot(self, *args, **kwargs):
        """
        Plot the Traces showing one graph per Trace.

        Plots the whole time series for self.max_npts points and less. For more
        points it plots minmax values.
        """
        stream_new = []
        # Just remove empty traces.
        if not self.automerge:
            if self.stream:
                for tr in self.stream:
                    stream_new.append([])
                    if len(tr.data):
                        stream_new[-1].append(tr)
        else:
            # Generate sorted list of traces (no copy)
            # Sort order: id, starttime, endtime
            ids = self.__get_mergable_ids()
            for id in ids:
                stream_new.append([])
                if self.stream:
                    for tr in self.stream:
                        tr_id = self.__get_merge_id(tr)
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

        make_subplots(rows=len(stream_new), cols=1, shared_xaxes=True,
                      vertical_spacing=0, figure=self.fig)
        # Create helper variable to track ids and min/max/mean values.
        self.ids = []
        # Loop over each Trace and call the appropriate plotting method.
        self.axis = []
        for _i, tr in enumerate(stream_new):
            # Each trace needs to have the same sampling rate.
            sampling_rates = {_tr.stats.sampling_rate for _tr in tr}
            if len(sampling_rates) > 1:
                msg = "All traces with the same id need to have the same " + \
                      "sampling rate."
                raise Exception(msg)
            sampling_rate = sampling_rates.pop()
            # if _i == 0:
            #    sharex = None
            # else:
            #    sharex = self.axis[0]
            # axis_facecolor_kwargs = dict(facecolor=self.background_color)
            # ax = self.fig.add_subplot(len(stream_new), 1, _i + 1,
            #                          sharex=sharex, **axis_facecolor_kwargs)
            ax = _i + 1
            self.axis.append(ax)
            # XXX: Also enable the minmax plotting for previews.
            method_ = self.plotting_method
            if method_ is None:
                if ((self.endtime - self.starttime) * sampling_rate >
                        self.max_npts):
                    method_ = "fast"
                else:
                    method_ = "full"
            method_ = method_.lower()
            if method_ == 'full':
                self.__plot_straight(stream_new[_i], ax, *args, **kwargs)
            elif method_ == 'fast':
                self.__plot_min_max(stream_new[_i], ax, *args, **kwargs)
            else:
                msg = "Invalid plot method: '%s'" % method_
                raise ValueError(msg)

        # for _i in range(len(stream_new)):
            # ax.text(0.02, 0.95, self.ids[_i], transform=ax.transAxes,
            #        fontdict=dict(fontsize="small", ha='left', va='top'),
            #        bbox=dict(boxstyle="round", fc="w", alpha=0.8))
            self.fig.add_annotation(text=self.ids[_i], xref='x domain',
                                    x=0.004, yref='y domain', y=0.98,
                                    row=_i + 1, col=1, showarrow=False,
                                    bgcolor='white', bordercolor='black')

        # Set ticks.
        # self.__plot_set_x_ticks()
        # self.__plot_set_y_ticks()
        # xmin = self._time_to_xvalue(self.starttime)
        # xmax = self._time_to_xvalue(self.endtime)
        # ax.set_xlim(xmin, xmax)
        # self._draw_overlap_axvspan_legend()

    def __plot_straight(self, trace, ax, *args, **kwargs):  # @UnusedVariable
        """
        Just plots the data samples in the self.stream. Useful for smaller
        datasets up to around 1000000 samples (depending on the machine on
        which it's being run).

        Slow and high memory consumption for large datasets.
        """
        # trace argument seems to actually be a list of traces..
        st = Stream(trace)
        # self._draw_overlap_axvspans(st, ax)
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
            if self.type == 'relative':
                # use seconds of relative sample times and shift by trace's
                # start time, which was set relative to `reftime`.
                x_values = (
                    trace.times() + (trace.stats.starttime - self.reftime))
            else:
                # convert seconds of relative sample times to days and add
                # start time of trace.
                # x_values = ((trace.times() / SECONDS_PER_DAY) +
                #            date2num(trace.stats.starttime.datetime))
                # Tho: this below should be double checked
                x_values = np.array(
                    trace.stats.starttime.ns + trace.times() * 1_000_000_000,
                    dtype='datetime64[ns]'
                )
            # ax.plot(x_values, trace.data, color=self.color,
            #        linewidth=self.linewidth, linestyle=self.linestyle)
            # self.fig.add_scatter(x=x_values, y=trace.data, row=ax, col=1,
            # showlegend=False, line_color='blue', hoverinfo='skip')
            self.fig.add_scatter(x=x_values, y=trace.data, row=ax, col=1,
                                 showlegend=False, hoverinfo='skip')
        # Write to self.ids
        # trace = st[0]
        trace = st.traces[0]
        if trace.stats.get('preview'):
            tr_id = trace.id + ' [preview]'
        elif hasattr(trace, 'label'):
            tr_id = trace.label
        else:
            tr_id = trace.id
        self.ids.append(tr_id)

    def __plot_min_max(self, trace, ax, *args, **kwargs):  # @UnusedVariable
        """
        Plots the data using a min/max approach that calculated the minimum and
        maximum values of each "pixel" and then plots only these values. Works
        much faster with large data sets.
        """
        # self._draw_overlap_axvspans(Stream(trace), ax)
        # Some variables to help calculate the values.
        starttime = self._time_to_xvalue(self.starttime)
        endtime = self._time_to_xvalue(self.endtime)
        # The same trace will always have the same sampling_rate.
        sampling_rate = trace[0].stats.sampling_rate
        # width of x axis in seconds
        x_width = endtime - starttime
        # normal plots have x-axis in days, so convert x_width to seconds
        if self.type != "relative":
            x_width = x_width * SECONDS_PER_DAY
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
            if self.type != "relative":
                remaining_seconds /= SECONDS_PER_DAY
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
            start = self._time_to_xvalue(tr.stats.starttime)
            end = self._time_to_xvalue(tr.stats.endtime)
            if remaining_samples:
                # the last minmax pair is inconsistent regarding x-spacing
                x_values = np.linspace(start, end - remaining_seconds,
                                       num=extreme_values.shape[0] - 1)
                x_values = np.concatenate([x_values, [end]])
            else:
                x_values = np.linspace(start, end, num=extreme_values.shape[0])
            x_values = np.repeat(x_values, 2)
            y_values = extreme_values.flatten()
            # ax.plot(x_values, y_values, color=self.color)

            x_values_plotly = np.array(x_values * SECONDS_PER_DAY,
                                       dtype='datetime64[s]')
            self.fig.add_scatter(x=x_values_plotly, y=y_values, row=ax, col=1,
                                 showlegend=False, hoverinfo='skip')

        # remember xlim state and add callback to warn when zooming in
        self._initial_xrange = (self._time_to_xvalue(self.endtime) -
                                self._time_to_xvalue(self.starttime))
        self._minmax_plot_xrange_dangerous = False
        # ax.callbacks.connect("xlim_changed", self._warn_on_xaxis_zoom)
        # set label, write to self.ids
        if hasattr(trace[0], 'label'):
            tr_id = trace[0].label
        else:
            tr_id = trace[0].id
        self.ids.append(tr_id)

    def __setup_figure(self):
        """
        The design and look of the whole plot to be produced.
        """
        # import matplotlib.pyplot as plt
        # Setup figure and axes
        # self.fig = plt.figure(num=None, dpi=self.dpi,
        #                      figsize=(float(self.width) / self.dpi,
        #                               float(self.height) / self.dpi))

        # if hasattr(self.stream, 'label'):
        #     suptitle = self.stream.label
        # elif self.type == 'relative':
        #     suptitle = ("Time in seconds relative to %s" %
        #                 _timestring(self.reftime))
        # elif self.type == 'dayplot':
        #     suptitle = '%s %s' % (self.stream[0].id,
        #                           self.starttime.strftime('%Y-%m-%d'))
        # elif self.type == 'section':
        #     suptitle = 'Network: %s [%s] - (%i traces / %s)' % \
        #         (self.stream[-1].stats.network,
        #          self.stream[-1].stats.channel,
        #          len(self.stream), _timestring(self.starttime))
        # else:
        #     # suptitle = '%s  -  %s' % (_timestring(self.starttime),
        #     #                          _timestring(self.endtime))
        #     suptitle=f"{self.starttime.ctime()} - {self.endtime.ctime()}"
        suptitle = f"{self.starttime.ctime()} - {self.endtime.ctime()}"
        # add suptitle
        # y = (self.height - 15.0) / self.height
        # self.fig.suptitle(suptitle, y=y, fontsize='small',
        #                  horizontalalignment='center')

        title = {
            'text': suptitle,
            'x': 0.5,
            'xanchor': 'center',
            'font_size': 24
        }
        # layout = go.Layout(height=self.height, width=self.width, title=title)
        layout = go.Layout(height=self.height, width=self.width, title=title,
                           font_color="black", font_size=20,
                           margin=dict(l=120))
        self.fig = go.Figure(layout=layout)

        # XXX: Figure out why this is needed sometimes.
        # Set size and dpi.
        # self.fig.set_dpi(self.dpi)
        # self.fig.set_figwidth(float(self.width) / self.dpi)
        # self.fig.set_figheight(float(self.height) / self.dpi)

    def _warn_on_xaxis_zoom(self, ax):
        """
        Method to be used as a callback on `method=fast`, "minmax"-type plots
        to warn the user when zooming into the plot.
        """
        xlim = ax.get_xlim()
        if xlim[1] - xlim[0] < 0.9 * self._initial_xrange:
            dangerous = True
        else:
            dangerous = False
        if dangerous and not self._minmax_plot_xrange_dangerous:
            self._add_zoomlevel_warning_text()
        elif self._minmax_plot_xrange_dangerous and not dangerous:
            self._remove_zoomlevel_warning_text()
        self._minmax_plot_xrange_dangerous = dangerous

    def _add_zoomlevel_warning_text(self):
        return
        # Todo
        # ax = self.fig.axes[0]
        # self._minmax_warning_text = ax.text(
        #    0.95, 0.9, MINMAX_ZOOMLEVEL_WARNING_TEXT, color="r",
        #    ha="right", va="top", transform=ax.transAxes)

    def _remove_zoomlevel_warning_text(self):
        return
        # Todo
        # ax = self.fig.axes[0]
        # if self._minmax_warning_text in ax.texts:
        #    self._minmax_warning_text.remove()
        # self._minmax_warning_text = None

# TODO
# def _draw_overlap_axvspans(self, st, ax):
#     for _, _, _, _, start, end, delta, _ in st.get_gaps():
#         if delta > 0:
#             continue
#         start = self._time_to_xvalue(start)
#         end = self._time_to_xvalue(end)
#         self._overlap_axvspan = \
#             ax.axvspan(start, end, color="r", zorder=-10, alpha=0.5)

# def _draw_overlap_axvspan_legend(self):
#     if hasattr(self, "_overlap_axvspan"):
#         self.fig.axes[-1].legend(
#             [self._overlap_axvspan], ["Overlaps"],
#             loc="lower right", prop=dict(size="small"))

    def _time_to_xvalue(self, t):
        if self.type == 'relative':
            return t - self.reftime
        else:
            return date2num(t.datetime)


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
