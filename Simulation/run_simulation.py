# Runs the simulation 20 times and saves all CSV files

import subprocess

count = 1
total = 5

while (count <= total):
    script_path = "Simulation.py"
    arg = str(count)
    print("Running simulation " + str(count) + "/" + str(total))
    subprocess.run(["python", script_path, arg])
    count += 1
