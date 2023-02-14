# This script is used to download new raw MORPH files, and convert them to rinex format
# The rinex format consists in an .o file for Observational Data and a .h for Geo Navigation Data
# Both .o and .h files are plain text ones written in a pre defined format
# This relies on wine and the bin2std.exe converter

import datetime
import utils                         # Import all variables set in the configuration.py file
import configuration
import os

# Has a good practice, first check if all the relevant paths exists and are in order, i.e, are directories
# and not files or anything else
if not os.path.exists(configuration.input_path):
    # Raise an exception if the original folder doesn't exist
    raise Exception("Cannot get ZZ06 original files! " + configuration.input_path + " does not exist.")
elif os.path.exists(configuration.input_path) and not os.path.isdir(configuration.input_path):
    # Or if it exists but it is a file instead
    raise Exception("The original ZZ06 files path " + configuration.input_path + " exists but is not a directory!")
else:
    pass

# Get a list of receivers. The input_path is a global variable defined in the configuration.py file. Apparently just by
# importing it in the beginning of this file, all the variables there become accessible
receivers = os.listdir(configuration.input_path)
receivers.sort()

# This is a good time to check if the archive directory exists, along with all the sub folders and
# create them if not
utils.create_folder_if_necessary(configuration.input_archive_path)

# Same thing for the rinex data folder where the processed files should be stored
utils.create_folder_if_necessary(configuration.rinex_path)

# The ZZ06 receiver is the Trimble receiver so needs a different script
try:
    receivers.remove("ZZ06")
except ValueError:
    pass


for receiver in receivers:
    # Get list of all raw files from this receiver
    data_files = os.listdir(configuration.input_path + "/" + receiver)						# List all data files from each receiver

    # Protect against empty folders
    if len(data_files) == 0:
        continue
    # Filter using a lambda expression: retrieve last 4 characters
    # from the file name and compare them to a 4 character string
    data_files = filter(lambda input_file: input_file[-4:] == '.dat', data_files)
    data_files.sort()															# Sort them (probably alphabetically)

    # Work out period covered by these files. Assumes a filename format as YYYY-mm-dd
    # Extract the fist 10 characters from the first filename in the list, i.e, date from the oldest file
    start_date = data_files[0][:10]
    end_date = data_files[-1][:10]												# Same thing but now for the newest file
    print ("Receiver ", receiver, " data range ", start_date, end_date)


# Generate list of days between start and end
    start_year = data_files[0][:4]												# Extract the start year
    start_month = data_files[0][5:7]											# And now the month
    start_day = data_files[0][8:10]												# And finally the day

    end_year = data_files[-1][:4]												# Same thing for the end date
    end_month = data_files[-1][5:7]
    end_day = data_files[-1][8:10]

    # And now create proper datetime objects from the values extracted
    start_date = datetime.datetime(int(start_year), int(start_month), int(start_day))
    end_date = datetime.datetime(int(end_year), int(end_month), int(end_day))

    # Create an iterator for all the data days, i.e, creates an entry for each data day, in a datetime format
    # Its a fancy way to create all elements of the set from the start and end element.
    # NOTE: the end day is out of the set
    data_days = [i for i in utils.day_interval(start_date, end_date, datetime.timedelta(days=1))]

    # generate a list of files to process, only 1 per day
    process_files = []
    for day in data_days:
        date_format = day.strftime("%Y-%m-%d")								# Format the date in the filename format: YYYY-mm-dd
        # Select only the files from the day in question
        files = filter(lambda day_file: date_format == day_file[:10], data_files)
        # And get rid of any files produced around midnight, 2300 hours to be more precise.
        # In the data filename, the created time comes after the date
        files = filter(lambda day_file: day_file[11:13] != "23", files)

        if len(files) > 1:
            # Remove duplicates, only process the largest file
            # Creates a set with all file paths for the files with the same day
            s = [os.path.getsize(utils.get_raw_file_path(receiver, data_file)) for data_file in files]
            process_files.append(files[s.index(max(s))])						# And process only the largest of them, if multiple
        else:
            process_files.append(files[0])									# Otherwise, try to add the only element of the set

    # Before doing anything on a folder, check it it exists first and create it if not
    utils.create_folder_if_necessary(configuration.rinex_path + "/" + receiver)

    # At this point I have a set of files inside process_files that has
    # the biggest file in each day to be processed for each data day
    # Generate a list of files that have already been processed
    # Extract only characters 4 to 8 from the processed filename
    existing_files = [x[4:8] for x in os.listdir(configuration.rinex_path + "/" + receiver)]
    existing_files.sort()														# And sort them alphabetically

    # Process the new files, convert them to rinex
    for process_file in process_files:
        if utils.normalize_day_of_the_year(process_file) not in existing_files:				# Check for files already processed
            # Print the command to execute
            print ("CMD wine " + configuration.bin2std_path + " " + utils.get_raw_file_path(receiver, process_file))
            # And execute the .exe file using wine
            os.system("wine " + configuration.bin2std_path + " " + utils.get_raw_file_path(receiver, process_file))
            # The bin2std.exe application consumes a .dat file (raw GPS files) and produces two files: a .h file, wich
            # is a Geo Navigation Data and a .o file, which stands for Observation Data. The application extracts the
            # date from the filename and writes the processed files using the logic 0<year>_<day_of_the_year>.<year>.o/h
            # where <day_of_the_year> is a normalized string with 4 characters containing the order number of the day
            # for that year with a leading zero. That's why we need the normalize_day_of_the_year function bellow.
            # And move the processed files into the correct directory, with a new name change
            os.system("mv *" + utils.normalize_day_of_the_year(process_file) + "* " + utils.get_processed_files_path(receiver))
        else:
            print ("Skipping file: ", process_file)

    # Processing done. All relevant data is now in rinex type files in the rinex data folder
    # As a cleanup duty, lets move the raw gps files into the archive folder
    # First lets repeat the process from the beginning for each individual archive folder
    receiver_archive_path = configuration.input_archive_path + "/" + receiver

    # Again, first check for the improbable situation of a file existing instead of the designated path
    utils.create_folder_if_necessary(receiver_archive_path)

    # If no exception was raised by the previous command, it means that the receiver_archive_path either
    # already exists or it was just created. In any case we can move the raw gps files there now
    os.system("mv " + configuration.input_path + "/" + receiver + "/* " + receiver_archive_path)
