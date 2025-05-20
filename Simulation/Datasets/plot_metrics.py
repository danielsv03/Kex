# Plots graphs from averaged values.
# Looking for files: AuctionBased.csv, PriorityBased.csv, TimeBased.csv, Zipper.csv

import pandas as pd
import matplotlib.pyplot as plt

def main():
    csv_files = ["AuctionBased.csv", "PriorityBased.csv", "TimeBased.csv", "Zipper.csv"]
    
    # List of metrics that we expect to plot.
    # (If your CSV files include a 'Time Step' column, it will be used for the x-axis.
    # Otherwise, the index of the DataFrame is used.)
    metrics = [
        "Throughput",
        "Avg Passing Time",
        "Avg Stationary Duration",
        "Stop Count",
        "Fairness",
        "Stability (Speed Deviation)"
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
            
            plt.plot(x, y, label=file)
        
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
