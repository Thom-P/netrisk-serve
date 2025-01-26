""" Temporary (hacky) script to convert myo files to mseed

To be replaced by a proper package from Myotis.
"""

import struct
import sys

from obspy.core import UTCDateTime, Stream, Trace
import numpy as np


def convert(fname):

    # Parse station and sensor headers
    with open(fname, 'rb') as file:  # should use uint instead of int...
        #  crc = int.from_bytes(file.read(4), 'little')
        #  version = int.from_bytes(file.read(2), 'little')
        started_time = int.from_bytes(file.read(8), 'little')  # unix stamp (s)
        subsec = int.from_bytes(file.read(4), 'little')  # us
        #  uid = int.from_bytes(file.read(4), 'little')
        tick_time = int.from_bytes(file.read(8), 'little')  # ns
        sensor_count = int.from_bytes(file.read(2), 'little')
        station_name = ''
        while (c := file.read(1)) != b'\x00':
            station_name += c.decode('ascii')

        # Parse sensor headers
        id = [0] * sensor_count
        saving_ticks = [0] * sensor_count
        calib_0 = [0] * sensor_count
        calib_1 = [0] * sensor_count
        coeff_0 = [0] * sensor_count
        coeff_1 = [0] * sensor_count

        for sensor in range(sensor_count):
            id[sensor] = int.from_bytes(file.read(2), 'little')
            saving_ticks[sensor] = int.from_bytes(file.read(8), 'little')
            # unpack all in one shot instead?
            calib_0[sensor] = struct.unpack('<f', file.read(4))
            calib_1[sensor] = struct.unpack('<f', file.read(4))
            coeff_0[sensor] = struct.unpack('<f', file.read(4))
            coeff_1[sensor] = struct.unpack('<f', file.read(4))

        # Parse data (only valid if equal saving tick)
        raw_data = np.frombuffer(file.read(), dtype=np.uint8)
        raw_data.shape = (-1, 8 + 4 * sensor_count)

        raw_clock = raw_data[:, :8].flatten()
        # number of ticks since beginning of measure (to be confirmed)
        clock = np.frombuffer(raw_clock, np.uint64)
        first_tick_n = clock[0]

        data = []
        dtype = np.dtype(np.int32)  # apparently counts are signed
        dtype.newbyteorder('<')
        for sensor in range(sensor_count):
            raw_sensor = raw_data[:, 8 + sensor * 4:8 + (sensor + 1) * 4].flatten()
            data.append(np.frombuffer(raw_sensor, dtype))  # looks like it's copied

    # Convert to Obspy format and to quick deconv
    time_first_tick = UTCDateTime(started_time + subsec / 1_000_000 + first_tick_n * tick_time / 1_000_000_000)
    # time_first_tick = UTCDateTime.now()

    # print(subsec, first_tick_n * tick_time / 1_000_000_000)
    # print(time_first_tick)
    # print(coeff_1[0], coeff_0[0])

    net, sta, loc, cha_str = station_name.split('.')
    channels = cha_str.split('_')
    # print(net, sta, loc, cha_str, channels)
    head = {'network': net, 'location': loc, 'station': sta, 'starttime': time_first_tick, 'delta': tick_time / 1_000_000_000}

    for sensor in range(sensor_count):
        cha = channels[sensor]
        head['channel'] = cha
        st = Stream(Trace(data=data[sensor], header=head))
        # trace = data[0].astype(np.float64) * coeff_1[0] + coeff_0[0]  
        # tr_myo = Trace(data=trace, header=head)
        # print(head)
        mseed_name = '.'.join((net, sta, loc, cha, str(time_first_tick.ns), 'mseed'))
        st.write('/usr/local/app/mseed_segments/' + mseed_name)

    # tr_myo.plot()
    # tr_mseed.plot()

    '''
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(tr_myo.times("matplotlib"), tr_myo.data, "b-")
    #ax.plot(tr_mseed.times("matplotlib"), tr_mseed.data, "r+")
    ax.xaxis_date()
    fig.autofmt_xdate()
    plt.savefig('testplot.png')
    '''


if __name__ == "__main__":
    myo_file = sys.argv[1]
    convert(myo_file)
