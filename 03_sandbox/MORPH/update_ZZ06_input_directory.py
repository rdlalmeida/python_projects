# This script uses a text based list of moved files to progressively update the list of Trimble GPS raw
# data files to be further processed. I think this as a necessity due to the unusual amount of data produced
# by these GPS units. By the end of the year, i.e, before this data is archived, the amount of data files is
# enormous. The regular units have their daily files archived at the and of processing to reduce the year
# long operation. Since the ZZ06 station gets its data from the LoH stock (retrieved directly from leo server)
# I can't simple move files around. As such I devised this devious but effective method.

from utils import *
import datetime

# Has a good practice, first check if all the relevant paths exists and are in order, i.e, are directories
# and not files or anything else
if not os.path.exists(zz06_original_path):
    # Raise an exception if the original folder doesn't exist
    raise Exception("Cannot get ZZ06 original files! " + zz06_original_path + " does not exist.")
elif os.path.exists(zz06_original_path) and not os.path.isdir(zz06_original_path):
    # Or if it exists but it is a file instead
    raise Exception("The original ZZ06 files path " + zz06_original_path + " exists but is not a directory!")
else:
    pass


def get_timestamp():
    return str(datetime.datetime.today())[0:-7]


# Let's do one more check for the input files folder, to which we will move the original files
create_folder_if_necessary(input_path + "/ZZ06")

zz06_input_path = input_path + "/ZZ06"                  # Define the ZZ06 input files path

# List of files already moved from the original path
already_moved_files = []

# Now lets check first if the file list file exists. If so, read it and populate the already_moved_files list,
# If not, create it and continue. The file is going to be populated further ahead
if os.path.exists(zz06_list_of_files) and os.path.isdir(zz06_list_of_files):
    # Raise an exception if, by any reason, the path exists but as a directory and not as a file.
    raise Exception("The file " + zz06_list_of_files + " exist but it is a directory, not a writable file!")
else:
    # The next command either creates an empty file if it doesn't exist already,
    # or open an existing one for append and read
    zz06_list = open(zz06_list_of_files, "a+")

# Read the first line in the file. If it is empty, it will read an empty string. No problem with that
try:
    # Try to read a line from the file list
    zz06_processed_file = zz06_list.readline()
except IOError:
    # If not possible, its because the file is still completely empty. As such, just return an empty string
    zz06_processed_file = ""

while zz06_processed_file != "":
    # First remove any leading newlines from the read filename
    zz06_processed_file = zz06_processed_file.replace("\n", "")
    already_moved_files.append(zz06_processed_file)         # Put a processed file in the list
    zz06_processed_file = zz06_list.readline()              # Get the next line

# Sort them from oldest to newest
already_moved_files.sort(reverse=False)

# Lets get now the list of files in the source folder
original_raw_files = os.listdir(zz06_original_path)

# If we are in the beginning of a new year, i.e, all lists and files are new
if len(already_moved_files) == 0:
    original_raw_files.sort(reverse=False)          # Put the file list back in its original order
    for raw_file in original_raw_files:
        # Move the file to the list of moved files
        os.system("cp -p " + zz06_original_path + "/" + raw_file + " " + zz06_input_path)
        print get_timestamp() + " Copied " + zz06_original_path + "/" + raw_file + " to " + zz06_input_path

        zz06_list.write(raw_file + "\n")            # And write the copied file into the list
else:
    # Organize the already processed file in reverse order, i.e, from the most recent to oldest. Assuming that
    # our file processing is well done, we should only need to check these files until we find the one the
    # correspond to the last entry of the already moved file list
    original_raw_files.sort(reverse=True)
    last_moved_file = already_moved_files[-1]
    new_moved_files = []                    # Store the name of the moved files in the next loop here
    for raw_file in original_raw_files:
        # Compare the filename of the newest file with the last moved file in the list
        if raw_file != last_moved_file:
            # As long as they differ, it means that the file was not yet processed
            new_moved_files.append(raw_file)
            # So copy it to the right folder
            os.system("cp -p " + zz06_original_path + "/" + raw_file + " " + zz06_input_path)
            print get_timestamp() + " Copied " + zz06_original_path + "/" + raw_file + " to " + zz06_input_path
        else:
            print get_timestamp() + " Nothing to do for now. Exiting..."
            # Otherwise, we reach the part of the list that was already moved. If the order of the items
            # is correct, and it should be, it is pointless to carry on. All relevant files were moved
            # so far. Update the file list and get out of the loop then. We could have written the file
            # list before, but this way we can keep the chronological order.
            if len(new_moved_files) != 0:               # Check first if we moved any files
                new_moved_files.sort(reverse=False)     # Order the files from oldest to newest
                for new_moved_file in new_moved_files:
                    zz06_list.write(new_moved_file + "\n")
            else:
                pass
            break

    # We should never reach this point according to my logic, but anyhow, better safe than sorrow
    # I'm gonna add a couple of redundant lines, just in case
    if len(new_moved_files) != 0:
        new_moved_files.sort(reverse=False)             # Order the moved files from oldest to newest
        for new_moved_file in new_moved_files:
            # And update the file list
            zz06_list.write(new_moved_file + "\n")
    else:
        pass


zz06_list.close()               # Close the file. We are done here
