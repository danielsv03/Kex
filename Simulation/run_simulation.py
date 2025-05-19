# Runs the simulation 20 times and saves all CSV files

import subprocess

count = 1
total = 8

while (count <= total):
    script_path = "Simulation.py"
    arg = str(count)
    print("Running simulation " + str(count) + "/" + str(total))
    subprocess.run(["/usr/local/bin/python3", script_path, arg])
    count += 1