# At first glance, this module seems to be used only for drawing stuff in the html page
import datetime
import os
import configuration


# Method to remove undesirable characters from a list of elements. Useful to remove unwanted new lines,
# leading spaces, tabs and such
def clean_tokens(data_to_clean, chars_to_remove):
    # If empty arrays are send into the method
    if len(data_to_clean) <= 0:
        print "WARNING: Empty data to clean list. Nothing to do..."
        return data_to_clean

    if len(chars_to_remove) <= 0:
        print "WARNING: Empty characters to remove list. Nothing to do..."
        return data_to_clean

    new_data = []                           # String buffer to return

    for word_to_clean in data_to_clean:
        for char_to_remove in chars_to_remove:
            new_data.append(word_to_clean.strip(char_to_remove))

    return new_data


# Simple method to extract today's date and time
def get_timestamp():
    # Remove the millisecond part of today's datetime, to simplify things
    return str(datetime.datetime.today())[0:-7]


# Method to assert if today's the first day of the year
def is_new_year_day():
    # Extract today's month and day and compare it to January's first
    return str(datetime.datetime.today())[5:10] == "01-01"


# Generates the complete raw file path for the argument f
def get_raw_file_path(receiver, f=""):
    # Compose the path with the argument and path variables present in the configuration file
    return configuration.input_path + "/" + receiver + "/" + f


# Generate the complete processed file (rinex) path for the argument f
def get_processed_files_path(receiver, f=""):
    # Compose the path with the argument and path variables present in the configuration file
    return configuration.rinex_path + "/" + receiver + "/" + f


# This function gets a filename, extracts its date from it and return the number of the day of the year [1-366]
# I.e, 05-01-2016 yields 5 because its the fifth day of 2016
def day_of_the_year(s):
    year = int(s[:4])					# Extract the year and convert it to integer
    month = int(s[5:7])					# Same for the month
    day = int(s[8:10])					# And the day

    # Return the calculation of the order of the day in this date
    return datetime.datetime(year, month, day).timetuple().tm_yday


# This function normalizes the day of the year into a 4 character string. The number of days in the year for that data
# is leaded by a 0 and preceded by all zeros that it may need.
# E.g: 05-01-2016 => 0050, 08-11-2016 => 3130
def normalize_day_of_the_year(s):
    x = str(day_of_the_year(s))			# Get the order number of the day in the argument date
    while len(x) < 3:
        x = "0" + x						# Stuff it with leading zeros until the number of characters reaches 3

    return x + "0"						# And put a leading one before returning the string


# Simple function to retrive a string with the current year. Yet, since we are always processing things a
# day behind, i.e, on 2016-05-27 we process 2016-05-26 data,on new years day, I need to be careful with
# this fact.
def get_current_year():
    today_date = str(datetime.datetime.today())                 # Get current date
    if today_date[5:7] == "01" and today_date[8:10] == "01":    # If today is the 1st of January
        year = int(today_date[0:4])
        return str(year - 1)                                    # Return yesterday's year instead
    else:
        return today_date[0:4]                                  # Otherwise, extract the year value and return it


# Another even simpler function that returns the year's suffix, i.e, the last two digits of it
def get_current_year_suffix():
    return get_current_year()[2:4]


# Used for generating a list of days between start, end, of interval delta
def day_interval(day_start, day_end, delta):
    curr = day_start
    while curr < day_end:
        yield curr
        curr += delta


# This method checks if a path exists and if it does, also checks its type
# If it is a file, raise an exception, otherwise doesn't do anything
# If the folder pointed by the provided path doesn't exists, this method creates it
# Very useful to make sure that the folder structure in the project is kept up to date
def create_folder_if_necessary(folder_path):
    # First, check if the object pointed by the path already exists and if it does, check if it is a file
    if os.path.exists(folder_path) and not os.path.isdir(folder_path):
        # If a file exists in that path instead of a folder, raise the proper exception
        raise Exception("The path " + folder_path + " exists but it is a file, not a folder as supposed!")
    elif not os.path.exists(folder_path):
        os.makedirs(folder_path)                       # If nothing is there, create the folder
        print folder_path + " created."
    else:
        pass                                        # Otherwise, just ignore. This should occur 99.9999% of the time
