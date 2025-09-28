import os
import csv
import pandas as pd


def extract_user_stories(csv_file_path):
    """
    Extract all items from the 'user_story' column of a CSV file into a Python list.
    
    Args:
        csv_file_path (str): Path to the CSV file
    
    Returns:
        list: A list containing all values from the 'user_story' column
    
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        KeyError: If the 'user_story' column doesn't exist in the CSV
        Exception: For other potential errors during file reading
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Check if 'user_story' column exists
        if 'user_story' not in df.columns:
            raise KeyError("Column 'user_story' not found in the CSV file")
        
        # Extract the user_story column and convert to list
        # dropna() removes any NaN/null values
        user_stories = df['user_story'].dropna().tolist()
        
        return user_stories
        
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        raise Exception(f"Error reading CSV file: {str(e)}")

def append_to_links(filename, a, b):
    """
    Appends user story and QA link to links.csv file.
    
    Args:
        a (str): User story to append to user_story column
        b (str): QA link to append to qa_link column
    """
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(filename)
    
    # Open file in append mode
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers if file is new
        if not file_exists:
            writer.writerow(['user_story', 'qa_link'])
        
        # Write the data row
        writer.writerow([a, b])