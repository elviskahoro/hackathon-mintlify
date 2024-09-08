import pandas as pd
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
        measured_values = pd.read_csv(file_name, sep=';')
        measured_values.columns = ['station', 'temperature']
        logging.info(f"Data read into a DataFrame in {time.time() - start:.2f} seconds")
        
        logging.info(f"DataFrame info:\n{measured_values.info()}")
        logging.info(f"Sample of data:\n{measured_values.sample(5)}")
        
        # Group the data by station and calculate statistics
        start = time.time()
        grouped = measured_values.groupby('station')
        summary = grouped.agg({'temperature': ['min', 'mean', 'max']})
        summary['temperature', 'mean'] = summary['temperature', 'mean'].round(1)
        
        # Sort by station name
        summary = summary.sort_index()
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