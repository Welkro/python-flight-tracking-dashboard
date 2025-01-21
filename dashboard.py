import lightningchart as lc
import time
from math import radians, sin, cos, sqrt, atan2, degrees
from opensky_api import OpenSkyApi
from openSkyAccInfo import *

# Set LightningChart Python license key
lc.set_license('LICENSE_KEY')

# Initialize OpenSky API with credentials
api = OpenSkyApi(my_username, my_password)

# Target flight's ICAO24
target_icao24 = "4601f5"

# Reference point for Polar Chart (Helsinki Airport)
ref_lat, ref_lon = 60.317199707031, 24.963300704956 

# Initialize the dashboard
dashboard = lc.Dashboard(columns=5, rows=2, theme=lc.Themes.TurquoiseHexagon)

# Add Polar Chart for flight tracking
polar_chart = dashboard.PolarChart(column_index=0, row_index=0, row_span=2, column_span=3)
polar_chart.set_title("Flight Path Tracking")
polar_chart.get_amplitude_axis().set_title("Distance (km)")
polar_line_series = polar_chart.add_line_series()

# Add Line Chart for altitude over time
altitude_chart = dashboard.ChartXY(column_index=3, row_index=0, column_span=2)
altitude_chart.set_title("Altitude Over Time")
altitude_chart.get_default_y_axis().set_title("Altitude (m)")

# Dispose the default X-axis and replace it with linear-highPrecision
altitude_chart.get_default_x_axis().dispose()
x_axis = altitude_chart.add_x_axis(axis_type='linear-highPrecision')
x_axis.set_tick_strategy('DateTime')
x_axis.set_scroll_strategy('progressive')

altitude_line_series = altitude_chart.add_line_series(data_pattern='ProgressiveX')

# Configure basic gauge for altitude
altitude_gauge = dashboard.GaugeChart(column_index=3, row_index=1)
altitude_gauge.set_title("Current Altitude (m)")
altitude_gauge.set_angle_interval(start=180, end=0)  # Half-circle gauge
altitude_gauge.set_interval(start=0, end=15000)
altitude_gauge.set_value_indicator_thickness(0.01)
altitude_gauge.set_bar_thickness(6.0)
altitude_gauge.set_value_label_font(size=20)
altitude_gauge.set_tick_font(size=20)
altitude_gauge.set_needle_length(15.0)
altitude_gauge.set_needle_thickness(4.0)

# Configure basic gauge for velocity
velocity_gauge = dashboard.GaugeChart(column_index=4, row_index=1)
velocity_gauge.set_title("Current Velocity (m/s)")
velocity_gauge.set_angle_interval(start=180, end=0)  # Half-circle gauge
velocity_gauge.set_interval(start=0, end=500)
velocity_gauge.set_value_indicator_thickness(0.01)
velocity_gauge.set_bar_thickness(6.0)
velocity_gauge.set_value_label_font(size=20)
velocity_gauge.set_tick_font(size=20)
velocity_gauge.set_needle_length(15.0)
velocity_gauge.set_needle_thickness(4.0)

# Open the dashboard in live mode
dashboard.open(live=True)

# Helper functions
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    dlon = radians(lon2 - lon1)
    y = sin(dlon) * cos(radians(lat2))
    x = cos(radians(lat1)) * sin(radians(lat2)) - sin(radians(lat1)) * cos(radians(lat2)) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360

# Data storage
flight_path_data = []

# Main loop to fetch and update data
while True:
    try:
        # Fetch current states
        states = api.get_states()
        if states is None:
            print("Failed to fetch data from OpenSky API. Retrying...")
            time.sleep(5)  # Wait before retrying the API call
            continue

        # Find the target flight
        for s in states.states:
            if s.icao24 == target_icao24:
                print(f"Tracking {s.callsign}: Lat {s.latitude}, Lon {s.longitude}, Alt {s.geo_altitude}, Vel {s.velocity}, On Ground: {s.on_ground}")

                # Calculate distance and bearing for polar chart
                distance = haversine(ref_lat, ref_lon, s.latitude, s.longitude)
                angle = calculate_bearing(ref_lat, ref_lon, s.latitude, s.longitude)

                # Avoid adding duplicate points
                if len(flight_path_data) == 0 or (angle != flight_path_data[-1]['angle'] or distance != flight_path_data[-1]['amplitude']):
                    flight_path_data.append({'angle': angle, 'amplitude': distance})
                    polar_line_series.set_data(flight_path_data)  # Update chart

                # Update altitude and velocity
                altitude = s.geo_altitude
                velocity = s.velocity

                # Update altitude gauge and velocity gauge
                altitude_gauge.set_value(altitude)
                velocity_gauge.set_value(velocity)

                update_time_ms = int(time.time() * 1000)  # Use system time

                # Add altitude data to line chart
                if altitude is not None:
                    altitude_line_series.add(update_time_ms, altitude)

    except Exception as e:
        print(f"Error: {e}")

    # Wait before the next regular API call
    time.sleep(5)