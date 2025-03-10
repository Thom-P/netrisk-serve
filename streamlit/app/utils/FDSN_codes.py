import string

valid_chars = set(string.ascii_uppercase + string.digits + '-')

band_codes = {
    'J': 'fs > 5000',
    'F': '1000 ≤ fs < 5000, Tc ≥ 10',
    'G': '1000 ≤ fs < 5000, Tc < 10',
    'D': '250 ≤ fs < 1000, Tc < 10',
    'C': '250 ≤ fs < 1000, Tc ≥ 10',
    'E': 'Extremely Short Period, 80 ≤ fs < 250, Tc < 10',
    'S': 'Short Period, 10 ≤ fs < 80, Tc < 10',
    'H': 'High Broadband, 80 ≤ fs < 250, Tc ≥ 10',
    'B': 'Broadband, 10 ≤ fs < 80, Tc ≥ 10',
    'M': 'Mid Period, 1 < fs < 10',
    'L': 'Long Period, fs ~ 1',
    'V': 'Very Long Period, 0.1 ≤ fs < 1',
    'U': 'Ultra Long Period, 0.01 ≤ fs < 0.1',
    'W': 'Ultra-ultra Long Period, 0.001 ≤ fs < 0.01',
    'R': 'Extremely Long Period, 0.0001 ≤ fs < 0.001',
    'P': 'On the order of 0.1 to 1 day, 0.00001 ≤ fs < 0.0001',
    'T': 'On the order of 1 to 10 days, 0.000001 ≤ fs < 0.00001',
    'Q': 'Greater than 10 days, fs < 0.000001',
    'I': 'Irregularly sampled'
}

source_codes = {
    'H': 'High Gain Seismometer',
    'L': 'Low Gain Seismometer',
    'M': 'Mass Position Seismometer',
    'N': 'Accelerometer',
    'P': ('Geophone, very short period seismometer with natural frequency '
          '5 - 10 Hz or higher'),
    'A': 'Tilt Meter',
    'B': 'Creep Meter',
    'C': 'Calibration input',
    'D': 'Pressure',
    'E': 'Electronic Test Point',
    'F': 'Magnetometer',
    'I': 'Humidity',
    'J': 'Rotational Sensor',
    'K': 'Temperature',
    'O': 'Water Current',
    'G': 'Gravimeter',
    'Q': 'Electric Potential',
    'R': 'Rainfall',
    'S': 'Linear Strain',
    'T': 'Tide',
    'U': 'Bolometer',
    'V': 'Volumetric Strain',
    'W': 'Wind',
    'X': 'Derived or generated channel',
    'Y': 'Non-specific instruments',
    'Z': 'Synthesized Beams'
}

# need one category per source code...todo
subsource_codes = {
    'N, E, Z': 'North, East, Up',
    '1, 2, Z': 'Orthogonal components, nontraditional horizontals',
    '1, 2, 3': 'Orthogonal components, nontraditional orientations',
    'T, R': 'For rotated components or beams (Transverse, Radial)',
    'A, B, C': 'Triaxial (Along the edges of a cube turned up on a corner)',
    'U, V, W': 'Optional components, also used for raw triaxial output',
    'N': 'North',
    'E': 'East',
    'Z': 'Up',
    '1': 'Orthogonal components, nontraditional orientations',
    '2': 'Orthogonal components, nontraditional orientations',
    '3': 'Orthogonal components, nontraditional orientations',
    'T': 'For rotated components or beams (Transverse)',
    'R': 'For rotated components or beams (Radial)',
}
