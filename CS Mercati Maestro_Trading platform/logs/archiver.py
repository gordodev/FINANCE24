#!/usr/bin/env python3

# We import the tools (modules) we need for our script
import os                   # For working with operating system
import sys                  # For system-specific parameters and functions
import tarfile             # For creating compressed archive files
import logging             # For keeping track of what our script does
from datetime import datetime, timedelta  # For working with dates and times
from pathlib import Path   # For working with file paths in a way that works on all computers
import shutil              # For file operations like checking disk space

# These are our settings - we put them at the top so they're easy to find and change
# Think of these like adjustment knobs for our script
ARCHIVE_DIR = "archived_logs"     # The folder where we'll store our compressed files
LOG_FILE = "log_archiver.log"     # Where we'll write information about what our script did
FILE_AGE_DAYS = 7                 # How old a log file needs to be before we compress it
LOG_EXTENSION = ".log"            # What kind of files we're looking for

# Set up logging - this is like creating a diary for our script
# Every time something important happens, we write it down
logging.basicConfig(
    filename=LOG_FILE,            # Where to save our log messages
    level=logging.INFO,           # How detailed our logs should be
    format='%(asctime)s - %(levelname)s - %(message)s'  # How each log message should look
)

def setup_archive_dir():
    """
    Creates a folder to store our compressed files if it doesn't already exist.
    Like creating a new folder in Windows or Linux, but our script does it automatically.
    """
    archive_path = Path(ARCHIVE_DIR)
    # exist_ok=True means "don't complain if the folder is already there"
    archive_path.mkdir(exist_ok=True)
    return archive_path

def find_old_logs(start_path):
    """
    Looks through all folders starting from 'start_path' to find old log files.
    It's like a search party that:
    1. Looks in every folder and subfolder
    2. Checks each .log file's age
    3. Makes a list of the old ones
    """
    old_files = []  # Empty list to store the files we find
    
    # Calculate what date a file needs to be older than
    # For example, if FILE_AGE_DAYS is 7, this finds the date 7 days ago
    cutoff_date = datetime.now() - timedelta(days=FILE_AGE_DAYS)
    
    # Write in our log that we're starting to look for files
    logging.info(f"Searching for .log files older than {FILE_AGE_DAYS} days")
    
    # Path(start_path).rglob() is like a super-powered search
    # It looks through all folders and subfolders for files ending in .log
    for path in Path(start_path).rglob(f"*{LOG_EXTENSION}"):
        if path.is_file():  # Make sure it's a file and not a folder
            # Get when the file was created
            creation_time = datetime.fromtimestamp(path.stat().st_ctime)
            # If the file is older than our cutoff date, add it to our list
            if creation_time < cutoff_date:
                old_files.append(path)
    
    # Write in our log how many files we found
    logging.info(f"Found {len(old_files)} files to archive")
    return old_files

def create_archive(files, archive_dir):
    """
    Takes our list of old files and puts them in one compressed file (like a ZIP file).
    Think of it like putting many files into one big envelope to save space.
    """
    # If we didn't find any files, we don't need to create an archive
    if not files:
        logging.info("No files to archive")
        return None
    
    # Create a filename using the current date and time
    # This makes sure each archive has a unique name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"logs_{timestamp}.tar"
    archive_path = archive_dir / archive_name
    
    logging.info(f"Creating archive: {archive_path}")
    
    try:
        # Open a new tar archive file (like a ZIP file)
        # The 'with' statement makes sure we properly close the file when we're done
        with tarfile.open(archive_path, "w") as tar:
            # Add each file to our archive
            for file in files:
                tar.add(file, arcname=file.name)
        return archive_path
    except Exception as e:
        # If something goes wrong, write it in our log
        logging.error(f"Failed to create archive: {e}")
        return None

def verify_archive(archive_path, original_files):
    """
    Checks that all our files were correctly saved in the archive.
    It's like double-checking your homework before turning it in.
    """
    if not archive_path:
        return False
    
    logging.info("Verifying archive integrity")
    
    try:
        # Open our archive and check what's inside
        with tarfile.open(archive_path, "r") as tar:
            # Make sets of filenames for easy comparison
            # Sets are like lists but better for comparing groups of items
            archived_files = set(member.name for member in tar.getmembers())
            original_names = set(file.name for file in original_files)
            
            # Check if all our original files made it into the archive
            if not original_names.issubset(archived_files):
                logging.error("Archive verification failed: missing files")
                return False
            
            return True
    except Exception as e:
        logging.error(f"Archive verification failed: {e}")
        return False

def delete_original_files(files):
    """
    Deletes the original files after we're sure they're safely stored in our archive.
    Like cleaning your room after taking photos of everything.
    """
    logging.info("Deleting original files")
    
    for file in files:
        try:
            file.unlink()  # unlink() is Python's way of saying "delete this file"
            logging.info(f"Deleted: {file}")
        except Exception as e:
            logging.error(f"Failed to delete {file}: {e}")

def main():
    """
    This is where everything comes together - the main program that runs when we start our script.
    Think of it like a recipe that uses all the functions we defined above.
    """
    logging.info("Starting log archival process")
    
    try:
        # Check if we have enough space on the disk (at least 1GB free)
        if shutil.disk_usage(".").free < 1_000_000_000:  # 1GB in bytes
            logging.error("Insufficient disk space")
            return
        
        # Create our archive directory if it doesn't exist
        archive_dir = setup_archive_dir()
        
        # Find all the old log files
        current_dir = Path.cwd()  # cwd means "current working directory"
        old_files = find_old_logs(current_dir)
        
        if not old_files:
            logging.info("No files found to archive")
            return
        
        # Create the archive and verify it worked correctly
        archive_path = create_archive(old_files, archive_dir)
        if archive_path and verify_archive(archive_path, old_files):
            # Only delete the original files if everything worked perfectly
            delete_original_files(old_files)
            logging.info("Archive process completed successfully")
        else:
            logging.error("Archive process failed")
            
    except Exception as e:
        # If anything unexpected goes wrong, write it in our log
        logging.error(f"An unexpected error occurred: {e}")
    
    logging.info("Log archival process finished")

# This is a special Python idiom that means "only run this if this file is being run directly"
# (and not being imported by another Python script)
if __name__ == "__main__":
    main()
