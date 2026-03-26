import pandas as pd

# Load the CSV you already have
df = pd.read_csv("ProjectTrackerPP_Cleaned_NA.csv", low_memory=False)

# This command creates the ACTUAL physical file on your hard drive
df.to_parquet("ProjectTracker_Combined.parquet")

print("The physical file 'ProjectTracker_Combined.parquet' has been created in your folder!")