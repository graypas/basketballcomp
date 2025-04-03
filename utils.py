import os
import csv
import shutil
import pandas as pd

def delete_pycache(directory):
    pycache_path = os.path.join(directory, '__pycache__')
    if os.path.exists(pycache_path) and os.path.isdir(pycache_path):
        shutil.rmtree(pycache_path)
        print(f"Deleted __pycache__ folder in {directory}")
    else:
        print(f"No __pycache__ folder found in {directory}")

def initialize_folder(path, headers):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def validate_date(date):
    from datetime import datetime
    try:
        datetime.strptime(date, '%Y-%m-%d')
        return date
    except ValueError:
        raise ValueError("Date must be in the format YYYY-MM-DD.")
    
def write_to_csv(file_path, data):
    try:
        if isinstance(data, dict):
            data = [data]
        df = pd.DataFrame.to_csv(data)
        with open(file_path, 'w', newline='') as file_path:
            writer = csv.writer(file_path)
            for row in df:
                writer.writerow(row)

        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def validate_team_abbreviation(team):
    if len(team) != 3 or not team.isalpha():
        raise ValueError("Team abbreviation must be exactly 3 letters (e.g., 'NYK').")
    return team.upper()

def safe_float(value):
    try:
        if isinstance(value, str) and ":" in value:  # Handle time strings
            minutes, seconds = map(float, value.split(":"))
            return minutes + seconds / 60
        if isinstance(value, (int, float)):  # Already numeric
            return float(value)
        if isinstance(value, (list, tuple, dict)):  # Unexpected sequence
            print(f"Warning: Unexpected sequence, unable to convert: {value}")
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        print(f"Warning: Unable to convert to float: {value}")
        return 0.0

def convert_time_format(time_str):
    try:
        if "." in time_str and ":" not in time_str:
            parts = time_str.split(".")
            hours = int(parts[0])
            minutes = int(parts[1])
            total_minutes = hours * 60 + minutes
            return f"{total_minutes:02d}:00"
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                total_minutes = hours * 60 + minutes
                return f"{total_minutes:02d}:{seconds:02d}"
            elif len(parts) == 2:
                return time_str
        raise ValueError(f"Unexpected time format: {time_str}")
    except Exception as e:
        print(f"Error converting time: {time_str}, {e}")
        return "00:00"

def normalize_csv(file_path, output_path, time_column):
    try:
        df = pd.read_csv(file_path)
        if time_column in df.columns:
            df[time_column] = df[time_column].apply(convert_time_format)
            df.to_csv(output_path, index=False)
            print(f"Normalized CSV saved to {output_path}")
        else:
            raise KeyError(f"Column '{time_column}' not found in {file_path}")
    except Exception as e:
        print(f"Error normalizing CSV: {e}")

def prepare_csv(file_path):
    if os.path.exists(file_path):
        print(f"Clearing existing CSV: {file_path}")
    else:
        print(f"Creating new CSV: {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
