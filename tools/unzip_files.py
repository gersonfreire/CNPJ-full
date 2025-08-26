import os
import zipfile
import glob
import argparse
import sys

# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Unzip files from the downloads_cnpj directory, with options for handling existing files.",
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '--overwrite-all',
    action='store_true',
    help='Overwrite all existing files without asking.'
)
parser.add_argument(
    '--skip-all',
    action='store_true',
    help='Skip all existing files without asking (default non-interactive behavior).'
)
args = parser.parse_args()

if args.overwrite_all and args.skip_all:
    print("Error: --overwrite-all and --skip-all cannot be used at the same time.", file=sys.stderr)
    sys.exit(1)

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the source and destination directories
downloads_dir = os.path.join(script_dir, "downloads_cnpj")
unzip_dir = os.path.join(downloads_dir, "unziped")

# Create the destination directory if it doesn't exist
os.makedirs(unzip_dir, exist_ok=True)

# Find all zip files in the downloads directory
zip_files = glob.glob(os.path.join(downloads_dir, "*.zip"))

# Initialize flags from command-line arguments
overwrite_all = args.overwrite_all
skip_all = args.skip_all
is_interactive = not (overwrite_all or skip_all)

# Iterate over each zip file
for zip_path in zip_files:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                # Path for the extracted file
                extracted_file_path = os.path.join(unzip_dir, file_info.filename)

                # Check if the file already exists
                if os.path.exists(extracted_file_path):
                    if skip_all:
                        print(f"Skipping '{file_info.filename}' (skip all enabled).")
                        continue
                    
                    if overwrite_all:
                        # Proceed to extract without message
                        pass

                    elif is_interactive:
                        prompt = f"'{file_info.filename}' already exists. Overwrite? (y/n/a/s) (yes/no/all/skip all): "
                        answer = input(prompt).lower()

                        if answer == 'a':
                            overwrite_all = True
                        elif answer == 's':
                            skip_all = True
                            print(f"Skipping '{file_info.filename}' and all subsequent existing files.")
                            continue
                        elif answer != 'y':
                            print(f"Skipping '{file_info.filename}'.")
                            continue
                    else:
                        # Default non-interactive behavior is to skip
                        print(f"Skipping '{file_info.filename}' (default non-interactive behavior).")
                        continue
                
                # Extract the file
                print(f"Extracting '{file_info.filename}'...")
                zip_ref.extract(file_info, unzip_dir)

    except zipfile.BadZipFile:
        print(f"Error: '{zip_path}' is not a valid zip file. Skipping.")
    except Exception as e:
        print(f"An unexpected error occurred with '{zip_path}': {e}")

print("\nAll files have been processed.")