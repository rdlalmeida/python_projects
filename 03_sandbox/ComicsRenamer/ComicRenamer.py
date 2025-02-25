#  Another simple renaming script, this one to rename existing files through a convention (removing all non native name
# elements) and removing also those ridiculous and annoying last pages from the comics files.

import os
import sys
import rarfile
import re

bad_files = "files_to_remove_from_archive.txt"
bad_tokens = "tokens_to_remove_from_filename.txt"


# This one is going to be the main function for this case:
def rename_comics(path_to_folder):
    # Start by the usual: check if the path provided is legal
    if not os.path.isdir(path_to_folder):
        raise Exception("ERROR: The path provided " + path_to_folder + " is not a valid one.")

    list_of_files = os.listdir(path_to_folder)
    list_of_files.sort()

    for i in range(0, len(list_of_files)):
        print list_of_files[i]

        # If the file in question is indeed a file and not a folder
        if not (os.path.isdir(os.path.join(path_to_folder, list_of_files[i]))):
            remove_extra_pages(os.path.join(path_to_folder, list_of_files[i]), bad_files)

            # Split the file name for all spaces, underscores and dots that I can find
            tokens = re.findall(r"[^ ._]+", list_of_files[i])

            # Get the list with stuff to remove from the title
            elements_to_remove_from_title = tokenize_bad_elements_file(bad_tokens)

            # And now to purge the bad ones
            for element_to_remove_from_title in elements_to_remove_from_title:
                if element_to_remove_from_title in tokens:
                    tokens.remove(element_to_remove_from_title)

            # Concatenate the new title under the new_name variable, using a space as a separator
            new_name = ""
            for j in range(0, len(tokens) - 1):
                new_name += tokens[j] + ' '

            # Remove the trailing space
            new_name = new_name.strip()

            # And add the file extension
            new_name += "." + tokens[len(tokens) - 1]

            # And now, finally, rename the file
            os.system("mv " + escape_filename(os.path.join(path_to_folder, list_of_files[i])) + " " + escape_filename(os.path.join(path_to_folder, new_name)))
            print "Renaming " + escape_filename(os.path.join(path_to_folder, list_of_files[i])) + " to " + escape_filename(os.path.join(path_to_folder, new_name))

        else:
            # If a folder was found, than use our friendly recursivity to deal with all
            print "Going to check " + os.path.join(path_to_folder, list_of_files[i])
            rename_comics(os.path.join(path_to_folder, list_of_files[i]))


# Simple function to escape a couple of Linux troublesome characters so that the os.system calls can be made.
def escape_filename(old_filename):
    if len(old_filename) <= 0:
        raise Exception("ERROR: Invalid filename provided: " + str(old_filename))

    new_filename = old_filename.replace(' ', '\ ')
    new_filename = new_filename.replace('(', '\(')
    new_filename = new_filename.replace(')', '\)')
    new_filename = new_filename.replace("'", "\'")
    return new_filename


# Simple function that reads a file that sits in the same directory as this script and contains the names of all the
# images to remove from a given .cbr or .cbz archive file. Some people like to leave this annoying jpegs in the archive
# with lame publicity and loose exploits. I don't care for them as so I want to remove them from existence.
def tokenize_bad_elements_file(data_file):

    current_directory = os.getcwd()                 # Start by getting the current working directory where the file must be

    # Check if the file is around before anything else
    if not os.path.exists(os.path.join(current_directory, data_file)) or os.path.isdir(os.path.join(current_directory, data_file)):
        raise Exception("ERROR: The file " + os.path.join(current_directory, data_file) + " is not valid.")

    file_to_read = open(os.path.join(current_directory, data_file))     # If all goes well, get the damn file

    elements_to_remove = []                                             # I'm gonna store the stuff to remove here

    for line in file_to_read:
        elements_to_remove.append(line.strip())                         # Add all the lines from the file to the list

    return elements_to_remove                                           # Return the list for easier comparison


# This simple function removes that annoying page in each archive file. For security, I have to check first that only
# archived files, i.e, files with the cbz or cbr extension are analysed with this function
def remove_extra_pages(path_to_file, bad_files):
    if os.path.isdir(path_to_file):
        raise Exception("ERROR: The file path provided " + path_to_file + " is a directory!")

    if not rarfile.is_rarfile(path_to_file):
        raise Exception("The file provided " + path_to_file + " is not a valid one.")

    # If all is well all the way up to here, than lets start and analyse the archive file
    files_in_archive = rarfile.RarFile(path_to_file)            # Get the archive contents into an iterable structure

    files_to_remove_from_archive = tokenize_bad_elements_file(bad_files)

    # Go through each one of the archived files
    for file_in_archive in files_in_archive.infolist():
        # And also for each one of the files to remove
            # If a match was found
            archived_file = file_in_archive.filename.split('\\')[-1]
            if archived_file in files_to_remove_from_archive:
                # Remove the motherfucker from the archive without even unrar it
                print "Found " + archived_file + " in " + path_to_file
                os.system("rar d " + escape_filename(path_to_file) + " " + "*/" + escape_filename(archived_file) + " " + escape_filename(archived_file))
                # By some stupid reason, after the last command, the archive permissions got all weird. The next command
                # regenerates them
                os.system("chmod 777 " + escape_filename(path_to_file))


# This one simply makes sure that the main fucntion is called with the proper arguments
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception("ERROR: Wrong number of arguments provided: " + str(len(sys.argv)))

    rename_comics(sys.argv[1])

