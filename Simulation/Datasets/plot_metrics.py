import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

# Folder containing the CSV files
folder_path = "Datasets"

# Metrics to plot
metrics = ["Throughput", "Avg Waiting Time", "Avg Stop Time", "Fairness", "Stability", "Collision Count"]

# Get list of all CSV files in the folder
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

# Dictionary to store data
data = {}

# Read each CSV file and store the metrics
for file in csv_files:
    file_path = os.path.join(folder_path, file)
    df = pd.read_csv(file_path)

    # Store data under filename (without .csv)
    data[file.replace(".csv", "")] = df

# Plot each metric separately
for metric in metrics:
    plt.figure(figsize=(10, 6))  # Create a new figure

    for approach, df in data.items():
        if metric in df.columns:
            plt.plot(df.index, df[metric], marker='o', linestyle='-', label=approach)

    # Labels and title


def main():
    csv_files = ["AuctionBased.csv", "PriorityBased.csv", "TimeBased.csv", "Zipper.csv"]
    
    # List of metrics that we expect to plot.
    # (If your CSV files include a 'Time Step' column, it will be used for the x-axis.
    # Otherwise, the index of the DataFrame is used.)
    metrics = [
        "Throughput",
        "Avg Waiting Time",
        "Avg Stop Time",
        "Fairness",
        "Stability",
        "Collision Count"
    ]
    
    # Dictionary to hold DataFrames for each CSV file.
    data = {}
    for file in csv_files:
        try:
            # Read the CSV file into a DataFrame.
            df = pd.read_csv(file)
            data[file] = df
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    # For each metric, create a separate figure.
    for metric in metrics:
        plt.figure()
        for file, df in data.items():
            # Use the 'Time Step' column for x-axis if available, else use the DataFrame index.
            if "Time Step" in df.columns:
                x = df["Time Step"]
            else:
                x = df.index
            
            # Check if the metric exists in the DataFrame.
            if metric in df.columns:
                y = df[metric]
            else:
                print(f"Metric '{metric}' not found in file '{file}'.")
                continue
            
            plt.plot(x, y, marker='o', label=file)
        
        plt.xlabel("Time Step")
        plt.ylabel(metric)
        plt.title(f"{metric} over Time")
        plt.legend()
        plt.grid(True)
        # Save the figure (optional)
        plt.savefig(f"{metric.replace(' ', '_')}.png")
        plt.show()

if __name__ == "__main__":
    main()