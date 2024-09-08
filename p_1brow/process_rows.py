import polars as pl
import time
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_weather_data(file_name):
    logging.info(f"Reading file {file_name} into a DataFrame")
    total_time = time.time()

    try:
        start = time.time()
        # Read the file into a DataFrame
        measured_values = pl.read_csv(file_name, separator=';')
        measured_values.columns = ['station', 'temperature']
        logging.info(f"Data read into a DataFrame in {time.time() - start:.2f} seconds")
        
        # Log schema and sample
        logging.info(f"Schema:\n{measured_values.schema}")
        logging.info(f"Sample of data:\n{measured_values.head()}")
        
        # Group the data by station and calculate statistics
        start = time.time()
        grouped = measured_values.group_by('station').agg([
            pl.col('temperature').min().alias('min'),
            pl.col('temperature').mean().alias('mean'),
            pl.col('temperature').max().alias('max'),
        ])
        
        # Round the mean column to 1 decimal place
        summary = grouped.with_columns(pl.col('mean').round(1))
        
        # Sort by station name alphabetically
        summary = summary.sort('station')
        
        logging.info(f"Summary calculated in {time.time() - start:.2f} seconds")
        logging.info(f"Total time: {time.time() - total_time:.2f} seconds")
        logging.info(f"Summary of first 20 stations:\n{summary.head(20)}")
    
    except Exception as e:
        logging.error(f"Error processing file {file_name}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Usage: python script_name.py <file_name>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    process_weather_data(input_file)