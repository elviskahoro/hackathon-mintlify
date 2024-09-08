import duckdb
import time
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_weather_data(file_name):
    logging.info(f"Reading file {file_name} into a DuckDB table")
    total_time = time.time()

    try:
        # Create an in-memory DuckDB connection
        con = duckdb.connect(database=':memory:', read_only=False)
        
        # Timing the file read process
        start = time.time()
        con.execute(f"""
        CREATE TABLE measurements AS
        SELECT * FROM read_csv('{file_name}', columns=STRUCT_PACK(station := 'TEXT', temperature := 'DOUBLE'))
        """)
        logging.info(f"Data read into a DuckDB table in {time.time() - start:.2f} seconds")
        
        # Log the schema and sample data
        logging.info(f"Schema:\n{con.execute('DESCRIBE measurements').fetchall()}")
        logging.info(f"Sample of data:\n{con.execute('SELECT * FROM measurements LIMIT 5').fetchall()}")
        logging.info(f"Total number of measurements: {con.execute('SELECT count(*) FROM measurements').fetchone()[0]}")
        
        # Group data and calculate statistics
        con.execute("""CREATE VIEW grouped AS
                        SELECT
                        station,
                        MIN(temperature) AS min,
                        ROUND(AVG(temperature), 1) AS mean,
                        MAX(temperature) AS max
                        FROM measurements
                        GROUP BY station""")
        
        start = time.time()
        summary = con.execute("SELECT * FROM grouped ORDER BY station").fetchall()
        logging.info(f"Summary calculated in {time.time() - start:.2f} seconds")
        logging.info(f"Total time: {time.time() - total_time:.2f} seconds")
        
        # Log the first 20 stations' summary
        logging.info(f"Summary of first 20 stations:\n{summary[:20]}")
        
        # Close the connection
        con.close()

    except Exception as e:
        logging.error(f"Error processing file {file_name}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Usage: python script_name.py <file_name>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    process_weather_data(input_file)