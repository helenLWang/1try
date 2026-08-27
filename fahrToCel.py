# fahrToCel.py
# One script for the assignment. Currently includes Question 1 (a and b).

# ---------- Question 1a ----------
# Ask the user for a speed in miles per hour.
# input() always returns text, so float() turns it into a number.
mph = float(input("Enter a speed of an object in miles per hour (mph): "))

# Convert mph to meters per second.
# The assignment gives: 1 mph = 0.447 m/s
mps = mph * 0.447

# Print with labels and two decimal places, matching:
# 60.00 mph = 26.82 m/s
print(f"{mph:.2f} mph = {mps:.2f} m/s")

# ---------- Question 1b ----------
# Distance = speed * time.
# Speed is in m/s and time is 10 seconds, so distance is in meters.
time_seconds = 10
distance_meters = mps * time_seconds
print(f"Distance traveled in {time_seconds} seconds: {distance_meters:.2f} m")
