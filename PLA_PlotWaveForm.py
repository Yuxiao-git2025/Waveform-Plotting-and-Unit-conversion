"""
inventory (Inventory or None.) – Station metadata to use in search for adequate response.
If inventory parameter is not supplied, the response has to be attached to the trace beforehand.

Output units. One of:
"DISP"  displacement, output unit is meters

"VEL"  velocity, output unit is meters/second

"ACC"  acceleration, output unit is meters/second**2

"DEF"  default units, the response is calculated in output units/input units (last stage/first stage).
Useful if the units for a particular type of sensor (e.g., a pressure sensor) cannot be converted to displacement, velocity or acceleration.

water_level (float) – Water level for deconvolution.

pre_filt (list or tuple(float, float, float, float)) – Apply a bandpass filter in frequency domain to the data before deconvolution.
The list or tuple defines the four corner frequencies (f1, f2, f3, f4) of a cosine taper which is one between f2 and f3 and tapers
to zero for f1 < f < f2 and f3 < f < f4.

zero_mean (bool) – If True, the mean of the waveform data is subtracted in time domain prior to deconvolution.

taper (bool) – If True, a cosine taper is applied to the waveform data in time domain prior to deconvolution.

taper_fraction (float) – Taper fraction of cosine taper to use.

plot (bool or str) – If True, brings up a plot that illustrates how the data are processed in the frequency
domain in three steps.
First by pre_filt frequency domain tapering, then by inverting the instrument
response spectrum with or without water_level and finally showing data with inverted instrument response
multiplied on it in frequency domain. It also shows the comparison of raw/corrected data in time domain.
If a str is provided then the plot is saved to file (filename must have a valid image suffix recognizable by matplotlib e.g. ‘.png’)

"""

# =========================================================
from pathlib import Path
from obspy import read, read_inventory
# Input
station = "4O.CT01"
Time = "20250216"
channel = "HHZ"
tail="mseed"
# PATH
wave_root = Path("../FuncProcess/DirWave")
station_root = Path("../FuncProcess/DirSta")
# You can specify by yourself
wave_file = wave_root / f"{station}.{Time}.{channel}.{tail}"
station_file = station_root / f"{station}.xml"

# =========================================================
if not wave_file.is_file():
    raise FileNotFoundError(f"Waveform file not found:\n{wave_file}")
if not station_file.is_file():
    raise FileNotFoundError(f"Station XML file not found:\n{station_file}")
# Read wave and stations
st = read(str(wave_file))
inv = read_inventory(str(station_file))
print(st[0].stats) # Info
# =========================================================


# plot-1
st_orig = st.copy()
st_orig.plot( title='Original')

# plot-2
st_detrend = st.copy()
st_detrend.merge(method=1, fill_value="interpolate")
st_detrend.detrend("demean")
st_detrend.detrend("linear")
st_detrend.plot( title='Merged & Detrended')


# plot-3
# form='DISP'
# filterBand=(0.1, 0.2, 25.0, 30.0)
# level=60
# isplot=True
# st_rem=st.copy()
# st_rem.remove_response(inventory=inv, output=form, pre_filt=filterBand, water_level=level, plot=isplot)
# st_rem.plot()

# =========================================================

"""
Output Strings:

1 Trace(s) in Stream:
4O.CT01..HHZ | 2025-02-14T23:59:59.240000Z - 2025-02-16T00:00:01.155000Z | 200.0 Hz, 17280384 samples
         network: 4O
         station: CT01
        location: 
         channel: HHZ
       starttime: 2025-02-14T23:59:59.240000Z
         endtime: 2025-02-16T00:00:01.155000Z
   sampling_rate: 200.0
           delta: 0.005
            npts: 17280384
           calib: 1.0
         _format: MSEED
           mseed: AttribDict({'dataquality': 'D', 'number_of_records': 51374, 'encoding': 'STEIM1', 'byteorder': '>', 
                                                            'record_length': 512, 'filesize': 1048576})
"""