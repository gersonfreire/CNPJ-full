

import os
import zipfile
import glob

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the source and destination directories
downloads_dir = os.path.join(script_dir, "downloads_cnpj")
unzip_dir = os.path.join(downloads_dir, "unziped")

# Create the destination directory if it doesn't exist
os.makedirs(unzip_dir, exist_ok=True)

# Find all zip files in the downloads directory
zip_files = glob.glob(os.path.join(downloads_dir, "*.zip"))

# Initialize overwrite_all flag
overwrite_all = False

# Iterate over each zip file
for zip_path in zip_files:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                # Path for the extracted file
                extracted_file_path = os.path.join(unzip_dir, file_info.filename)

                # Check if the file already exists
                if os.path.exists(extracted_file_path) and not overwrite_all:
                    # Ask the user if they want to overwrite
                    prompt = f"'{file_info.filename}' already exists. Overwrite? (y/n/a): "
                    answer = input(prompt).lower()

                    if answer == 'a':
                        overwrite_all = True
                    elif answer != 'y':
                        print(f"Skipping '{file_info.filename}'...")
                        continue
                
                # Extract the file
                print(f"Extracting '{file_info.filename}'...")
                zip_ref.extract(file_info, unzip_dir)

    except zipfile.BadZipFile:
        print(f"Error: '{zip_path}' is not a valid zip file. Skipping.")
    except Exception as e:
        print(f"An unexpected error occurred with '{zip_path}': {e}")

print("\nAll files have been processed.")

