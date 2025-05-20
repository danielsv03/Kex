# Creates a csv file with average values from all runs of all strategies

import pandas as pd
import os
from glob import glob

# Define strategies and base path
strategies = ["AuctionBased", "PriorityBased", "TimeBased", "Zipper"]
base_path = os.path.dirname(__file__)  # Adjust this if needed

for strategy in strategies:
    # Find all files that match the pattern for the strategy
    pattern = os.path.join(base_path, f"{strategy}_*.csv")
    files = glob(pattern)

    if not files:
        print(f"No files found for strategy {strategy}")
        continue

    # Read all dataframes and store in a list
    dfs = [pd.read_csv(file, delimiter=',') for file in files]

    # Truncate all DataFrames to the shortest length
    min_length = min(df.shape[0] for df in dfs)
    dfs = [df.iloc[:min_length] for df in dfs]

    # Calculate the average
    avg_df = sum(dfs) / len(dfs)

    # Save to output file
    output_path = os.path.join(base_path, f"{strategy}.csv")
    avg_df.to_csv(output_path, index=False)

    print(f"Averaged data saved to {output_path}")
