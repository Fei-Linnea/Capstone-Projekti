import pandas as pd
from pathlib import Path

def main(snakemake):
    """Aggregate all feature CSV files into single Excel report"""
    
    print("Starting aggregation...")
    
    # Read all input CSV files
    dfs = []
    for csv_file in snakemake.input:
        df = pd.read_csv(csv_file)
        dfs.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Write to Excel
    combined_df.to_excel(snakemake.output[0], index=False, sheet_name='Features')
    
    print(f"Aggregation complete! Report saved to {snakemake.output[0]}")
    
    # Log completion
    with open(snakemake.log[0], 'w') as log:
        log.write(f"Aggregated {len(dfs)} files\n")
        log.write(f"Total subjects: {len(combined_df)}\n")

if __name__ == "__main__":
    main(snakemake)