# This routine converts the ZZ06 Trimble files into RINEX
# This is now automated on the Cambridge BSLCENE server so may be redundant if run in cbg
# This relies on the UNAVCO runpkr00 routine and teqc
# We use runpkr00 to convert the raw files to .dat format, and teqc to convert .dat to RINEX

# Data starts in zz06_path as .T01 files
# Then converted to .dat files in rinex_path/ZZ06
# Then converted to .rinex files in rinex_path/ZZ06

import os
import utils
import configuration         # For the datetime conversion routines

zz06_input_path = configuration.input_path + "/ZZ06"
zz06_rinex_processed_path = configuration.rinex_path + "/ZZ06"
zz06_t01_files_archive_path = configuration.input_archive_path + "/ZZ06/T01Files"
zz06_dat_files_archive_path = configuration.input_archive_path + "/ZZ06/datFiles"
# First check if the input folder exists and it is indeed a folder and not a file
if not os.path.exists(zz06_input_path):
    # This may happen because the script that moves files into the zz06 input folder has not yet run.
    # It's a small probability but it is possible
    raise Exception("The path " + zz06_input_path + " has yet to be created.")
elif not os.path.isdir(zz06_input_path):
    # If the path exists but it is a file instead of a directory
    raise Exception("The path " + zz06_input_path + " points to a file instead of a folder!")
else:
    pass

# Get list of all raw .t01 files from zz06
files = os.listdir(zz06_input_path)							            # List all files in the zz06 folder
files = filter(lambda zz06_file: zz06_file[-4:] == ".T01", files)		# Remove any file that do not have the .T01 extension
files.sort()										                    # And sort them alphabetically and chronologically

# Get a list of all the files already processed from the output path. These should be in .dat format
# Create the folder if it does not exist already and return an empty list if the folder does not exist or is empty
utils.create_folder_if_necessary(zz06_rinex_processed_path)
dat_files_already_processed = os.listdir(zz06_rinex_processed_path)

# Check if any files were found. Hopefully none should exist since this routine archives everything in the end
if len(dat_files_already_processed) > 0:
    # And filter for just the .dat files
    dat_files_already_processed = filter(lambda processed_dat_file:
                                         processed_dat_file[:4] != '.dat', dat_files_already_processed)

# Convert all files that haven't already been, to .dat format
for raw_file in files:
    if raw_file.replace("T01", "dat") not in dat_files_already_processed:
        print "Need to convert file ", raw_file
        print "Running " + configuration.runpkr00_path + " -v -g -d " + zz06_input_path + "/" +\
              raw_file + " " + zz06_rinex_processed_path + "/" + raw_file.replace("T01", "dat")
        os.system(configuration.runpkr00_path + " -v -g -d " + zz06_input_path + "/" + raw_file +
                  " " + zz06_rinex_processed_path + "/" + raw_file.replace("T01", "dat") + " > /dev/null")

# The ZZ06 files are split into hourly chunks that need to be combined into 24 files per day
# Trimble GPS stores a file each hour using the following format <Serial_number><hour_character>.dat
# This results in a 24 file rotation based on the last character of the file name, before the .dat or ,T01 extension
# The first file for a given day is stored as XXXXXXX0.T01, the second on as XXXXXXX1.T01, the 10th one as
# XXXXXXXA.T01 (using the alphabet now) and the 23rd one is going to be XXXXXXXN.T01
# The next file after this one is an increment of 1 from XXXXXXX and resumes the 0 as final character
# Example: file 3865122N.T01 is the last one to be stored before the new rotation. Next file name is going
# to be 365651230.T01
days = []										# Days is going to save several day structures
hours = []										# In an hours structure we collect hourly files from a single 24 h cycle
for time_file in files:
    if time_file[-5] == "0":					# Look for a cycle starting file
        days.append(hours)						# When got one, append the previous collection of files to a single
        hours = []								# Reset the buffer
    hours.append(time_file)						# Otherwise, just append a new hourly file to the existing day

days.append(hours)								# Append the rest of the unprocessed files
days = days[1:]									# Discard the first record [0] apparentely

# Now that all files are under the .dat format, lets proceed with the processing so that they can be transformed
# into .o files.

# Get a list of already processed files into the o format
o_processed_files = filter(lambda temp_file: "." + utils.get_current_year_suffix() + "o" in temp_file,
                           os.listdir(zz06_rinex_processed_path))
o_processed_files.sort()						# Sort them

# Remove all the files that were already processed from the working list. The days structure is going to have
# only the files whose name coincide with the respective .o file.
# This is how this works: the 24 hourly files for a given day are named <XXXX><NNN><H>.T01, where
# <XXXX> is a serial number that really doesn't matter for now
# <NNN> is a 3 digit number that is common to all files for that day. Next day files will have NNN+1 instead
# <H> is the digit that identifies the hour and goes from 0 to N as seen before
# The processed daily file is named with the format 0<current_year_suffix>_<NNN0>.<current_year_suffix>o,
# like for example 015_1220.15o for a 2015 file,
# where <current_year_suffix> is the last two digits of the current year and <NNN> is the sequential number
# from above
days = filter(lambda day_file: "0" + utils.get_current_year_suffix() + "_" + day_file[0][4:7] + "0." +
                               utils.get_current_year_suffix() + "o" not in o_processed_files, days)

print "Days to process:"    									# Show only which days are going to get processed
day_count = 0
for day in days:
    print "Day #" + str(day_count) + ": ",
    print day
    day_count += 1

for hours in days:
    # Convert this file to RINEX, with both the navigation and observation files
    print "Processing ", hours
    parameters = ["-tr d -week 1895 +nav temp.nav"]

    # Add the hourly files, in their processed .dat format, to the parameter list to be run
    for hour in hours:
        # This will indicate the teqc application to pick all 24 hourly files
        parameters.append(zz06_rinex_processed_path + "/" + hour.replace("T01", "dat"))

    # And process them into a single file called temp.rinex
    parameters.append(" > temp.rinex")

    # Printout the command that is going to be executed. The reduce command simply concatenates
    # all parameters in a single line, separated by a blank space as stated in the reduce function
    print "teqc " + reduce(lambda parameter, new_hour: parameter + " " + new_hour, parameters)

    # And then run them
    os.system("teqc " + reduce(lambda parameter, new_hour: parameter + " " + new_hour, parameters))

    # To retrieve the day of the year in question, simply pick one of the hourly files and extract it
    day_of_year = (hours[0])[4:7]

    # Compile the .o (observational) filename
    o_file_name = "0" + utils.get_current_year_suffix() + "_" + day_of_year + "0." +\
                  utils.get_current_year_suffix() + "o"
    # Compile the .n (Geo Navigation) file from the previous one
    n_file_name = o_file_name[0:-1] + "n"

    # Rename the temporary files into the processed files in the proper directory
    # The .rinex files becames the .o file and the .nav becames the .n
    os.system("mv temp.rinex " + zz06_rinex_processed_path + "/" + o_file_name)
    os.system("mv temp.nav " + zz06_rinex_processed_path + "/" + n_file_name)

# Finally, once we are done with the input files, let us move them to the archive folder to keep our working area clean
# Note that the ZZ06 raw files are the .T01 files from the GPS unit that are then converted to the .dat files that
# are going to be processed into .o, .h and .n files. The other MORPH receivers output the .dat files directly, Which
# means that, in order to keep consistency, we have to archive the ZZ06 raw files into two sub folders: T01 and dat

# First, the usual: check if the archive folder exists and create it if not
utils.create_folder_if_necessary(zz06_t01_files_archive_path)
utils.create_folder_if_necessary(zz06_dat_files_archive_path)


print "ZZ06 .T01 files processing complete.\nMoving .T01 input files to archive folder now..."
# Refresh the file list in the input folder
t01_files = os.listdir(zz06_input_path)
# Filter for just the .T01 terminanted files
t01_files = filter(lambda raw_file: raw_file[-4:] == ".T01", t01_files)

for t01_file in t01_files:
    # Just for safety, check if the file is still there first and it is a file
    if os.path.exists(zz06_input_path + "/" + t01_file) and \
            os.path.isfile(zz06_input_path + "/" + t01_file) and str(t01_file)[-4:] == ".T01":
        os.system("mv " + zz06_input_path + "/" + t01_file + " " + zz06_t01_files_archive_path)
        print "Moved " + zz06_input_path + "/" + t01_file + " to " + zz06_t01_files_archive_path + "/" + t01_file


print "ZZ06 .dat files processing complete.\nMoving .dat files to archive folder now..."
# Start by refreshing the dat file list
dat_files = os.listdir(zz06_rinex_processed_path)
# Filter for just the .dat terminated files
dat_files = filter(lambda dat_file: dat_file[-4:] == ".dat", dat_files)

for dat_file_to_move in dat_files:
    os.system("mv " + zz06_rinex_processed_path + "/" + dat_file_to_move + " " + zz06_dat_files_archive_path)
    print "Moved " + zz06_rinex_processed_path + \
          "/" + dat_file_to_move + " to " + zz06_dat_files_archive_path + "/" + dat_file_to_move
