import datetime
# This is the configuration file, where all the fixed paths are defined, as long as some constants


# Even though this is a purely constant filled document, I have to create a function at this point, in order
# to maintain part of the code flexible and avoid circular references at the same time
# Simple function the returns the current year, in the string format.
# I need it here to update some paths after new year's day. True story...

# Simple function to retrive a string with the current year. Yet, since we are always processing things a
# day behind, i.e, on 2016-05-27 we process 2016-05-26 data,on new years day, I need to be careful with
# this fact.
# There's a replicate function in utils.py but I've put this one instead of importing the utils.py file
# to avoid circular imports since utils.py already imports this one.
def config_get_current_year():
    today_date = str(datetime.datetime.today())                 # Get current date
    if today_date[5:7] == "01" and today_date[8:10] == "01":    # If today is the 1st of January
        year = int(today_date[0:4])
        return str(year - 1)                                    # Return yesterday's year instead
    else:
        return today_date[0:4]                                  # Otherwise, extract the year value and return it


# Base utils folder path
base_util_path = "/home/ricardoalmeida/morph/morph_processing/utils"

# Base path for the data storage structure
base_path = "/home/ricardoalmeida/morph"

# Base path for the processed data sub folders
#base_processing_path = "/data/morph/morph_processing"
base_processing_path = base_path + "/data_processing"

# Base path for the scripts location
scripts_path = "/home/ricardoalmeida/PycharmProjects/MORPH"

# Folder path for the ZZ06 Trimble files
#zz06_original_path = "/leo/" + config_get_current_year() + "/zz06"             # Use this one when running update_ZZ06_input_directory_leo.py
zz06_original_path = "/data/loh/data/" + config_get_current_year() + "/zz06"    # And this one when running update_ZZ06_input_directory_scp.py

# Path for the file that keeps the list of all the files moved to the input folder
zz06_list_of_moved_files = base_path + "/ZZ06_" + config_get_current_year() + "_moved_files"

# Location of raw data downloaded from MORPH receivers
input_path = base_path + "/raw_gps_data"

# Location of the archive folder for the raw GPS files
input_archive_path = base_path + "/archive/raw_gps_data"

# After converting the raw data into rinex, store the files in this folder
rinex_path = base_processing_path + "/rinex_data"

# Once done with the rinex files, move them to this archive forlder
rinex_archive_path = base_path + "/archive/rinex_data"

# After analysing the rinex files, store the output of the RTK analysis in this folder
rtk_path = base_processing_path + "/rtk_analysis"

# When the rtk files are no longer needed, move them here
rtk_archive_path = base_path + "/archive/rtk_analysis"

# Configuration file used by the rnx2rtk executable
rtk_config = base_util_path + "/morph.conf"

# Executable used to convert raw gps data into rinex files
bin2std_path = base_util_path + "/bin2std.exe"

# Executable necessary to tun the ZZ06 files
runpkr00_path = base_util_path + "/runpkr00"

# Executable for converting from rinex to rtkp files
rnx2rtkp_path = base_util_path + "/rnx2rtkp"

# After analysing the RTK output, store the movement records in this folder
output_path = base_path + "/movement_records"

html_path = base_processing_path + "/index.html"

origin = "S5"       # Unit in the start of base (South side)
end = "S8"          # Unit in the end of base (North side)
# These show which receivers are on which module. Note the order of these elements is important since it
# describes the position of the MORPH units from South to North.
modules = {"H2": ["S5", "S4"],
           "H1": ["ZZ06", "ZZ06"],
           "E2": ["S2", "S1"],
           "E1": ["S3", "S13"],
           "C": ["S9", "S10"],
           "B2": ["S7", "S8"]}

# These distances are used to calculate the error in the measurements - i.e. their separation shouldn't change
# Fixed_distances = [["S1","S2"],["S3","S13"],["S5","S4"],["S7","S8"],["S9","S10"]]. These are pairs of antennas
# set on the extremes of a single module. The modules aren't elastic and so these distances should be constant

# These distances are used to calculate the error in the measurements - i.e. their separation shouldn't change
fixed_distances = filter(lambda module: module != ["ZZ06", "ZZ06"], modules.values())
modules_in_order = ["S5", "S4", "ZZ06", "S2", "S1", "S3", "S13", "S9", "S10", "S7", "S8"]

# List of all the pairs of MORPH receivers that have gaps between them, i.e, those rubber sleeves that
# connect the modules and are supposed to move around once the modules shift their positions. The
# ["S1, S3"] element refers to the outside bridge between E1 and E2
gaps = [["S4", "ZZ06"], ["ZZ06", "S2"], ["S1", "S3"], ["S13", "S9"], ["S10", "S7"], ["S13", "S7"]]

# Generate a list of distances of interest
sites = list(set(sum(modules.values(), [])))

# Create a list of all the interesting combinations for this study.
# S13 is the central point of the MORPH units referential and as such all distances from this point
# are relevant. Then we have the gaps, which should measure the movement between modules, which is reflected
# in these rubber connections. The distances between each extreme of the base are relevant ([[origin, end]]).
# Finally we have the fixed distances more as a error control thing than anything else.
useful_distances = [["S13", site] for site in sites]		# Start by compiling all the distances to the central point
useful_distances.append([origin, end])						# Add the base lenght to it

# Now, add the remaining gaps and fixed distances elements but taking care that no redundant elements
# are inserted, i.e, duplicated and identical elements (For example, ["S13", "S7"] and ["S7", "S13"] are
# identical because they establish the distance between the same pair of receptors
for distance in gaps + fixed_distances:
    if distance not in useful_distances and [distance[1], distance[0]] not in useful_distances:
        useful_distances.append(distance)					# Add only non existing elements to the list

# Finally, remove any zero distance elements, i.e, pairs of the same receptor
for distance in useful_distances:
    if distance[0] == distance[1]:							# If both receptors are identical
        useful_distances.remove(distance)					# Remove them from the list

# These describe the location of the antenna from the center, and nearest end, of each module.
center_offset = {
    'S5': 0,
    'S4': 1866 / 2,
    'S2': 1205,
    'S13': 0,
    'S1': (7670 / 2) - 3200,
    'S3': (7670 / 2) - 3210,
    'S6': 0,
    'S7': -1 * ((7670 / 2) - 1300),
    'S8': -1 * ((7670 / 2) - 1300),
    'S9': 0,
    'S10': 0,
    'ZZ06': 3835
}

length_offset = {
    'S7': -2140,
    'S8': 2140,
    'ZZ06': (19200 / 2) - 1255,
    'S5': -4252,
    'S4': 1140,
    'S2': -3650,
    'S1': 3742,
    'S3': -3742,
    'S13': 2595,
    'S6': 0,
    'S9': -4701,
    'S10': 4701
}

height_offset = {
    'S5': -1870,
    'S4': -1120,
    'S2': -1120,
    'S13': -1120,
    'S1': -1120,
    'S3': -1120,
    'S6': -1120,
    'S7': 0,
    'S8': 0,
    'S9': -220,
    'S10': -220,
    'ZZ06': -1120
}


# These are used to draw the outlines of each module
# They are not critical
module_width = {
    'H2': 10,
    'H1': 10,
    'E2': 10,
    'b': 1.5,
    'E1': 10,
    'A': 13,
    'C': 10,
    'B1': 10,
    'B2': 10
}

module_length = {
    'H2': 19.2,
    'H1': 19.2,
    'E2': 19.2,
    'b': 20,
    'E1': 19.2,
    'A': 28.4,
    'C': 19.2,
    'B1': 19.2,
    'B2': 19.2
}

# This field should exist ONLY when there is no MORPH receivers on the module
approx_loc = {
    'H1': -63.5,
    'b': -25.5,
    'A': 18.7,
    'B1': 62.5
}

if __name__ == "__main__":
    print "Useful distances ", useful_distances
