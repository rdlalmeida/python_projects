# This one goes through a subtitle file, line by line, and removes any offending block of lines, i.e, a group of lines
# headed by a sequential line and a time line
# I'm going to get the main parameters through the command line for simplicity of sorts

import os
import types
import sys

# String used to separate subtitle blocks
block_separator = '\r\n'


# Here's the main function
def cleaner(path_to_dirty_subs, subs_extension):
    # Check if the provided path is valid
    if not os.path.isdir(path_to_dirty_subs):
        raise Exception("ERROR: The path provided: " + path_to_dirty_subs + " is invalid!")

    # Check if the extension provided is a valid one in length and in type
    if len(subs_extension) <= 0 or not isinstance(subs_extension, types.StringType):
        raise Exception("ERROR: The extension provided: " + subs_extension + " is invalid!")

    sub_files = os.listdir(path_to_dirty_subs)
    filter(lambda file: file[-len(subs_extension)] == subs_extension, sub_files)

    # Get the list with all the subtitle files to clean
    sub_files.sort()

    # And the list with trigger words
    black_list = load_words()

    # Now circle for all the subtitle files
    for i in range(0, len(sub_files)):
        if not os.path.isfile(os.path.join(path_to_dirty_subs, sub_files[i])):
            raise Exception("ERROR: The file" + os.path.join(path_to_dirty_subs, sub_files[i]) + " is invalid!")

        # Open the current file to read
        current_file = open(os.path.join(path_to_dirty_subs, sub_files[i]), "r+")
        tmp_file = open(os.path.join(path_to_dirty_subs, "tmp.txt"), "a+")

        # Get the first written line
        current_line = current_file.readline().strip("\n")

        # I'm going to operate on line blocks
        line_block = []

        # Run the loop until the EOF is reached
        while current_line != "":

            if current_line == block_separator:
                # If the line block is valid
                if not validate_block(line_block, black_list):
                    # Go through each line
                    for line in line_block:
                        # And write the line in the temporary file
                        tmp_file.write(line + "\n")
                    # Add a new line to the end of the subtitle block
                    tmp_file.write("\r\n")
                    tmp_file.flush()

                    # Reset the line block
                    line_block = []
                else:
                    # If the block comes out as invalid, discard it by reseting the current line block
                    line_block = []
            else:
                # Otherwise just add the current line to the current block and continue
                line_block.append(current_line.strip("\n"))

            # Get the next line
            current_line = current_file.readline()

        tmp_file.close()
        current_file.close()

        # And now, remove the original file
        os.system("rm -rf " + os.path.join(path_to_dirty_subs, sub_files[i].replace(' ', '\ ')))

        # And rename the temporary file as the original one
        os.system("mv " + os.path.join(path_to_dirty_subs, "tmp.txt") +
                  " " + os.path.join(path_to_dirty_subs, sub_files[i].replace(' ', '\ ')))


# Method to analyse a subtitle block. Basically go through each line and check if any of the black listed words is
# there. If yes, then return True and go from there. Else return False and proceed accordingly. Easy hun?
def validate_block(subtitle_block, black_list):

    # Go through all words inside the black list
    for black_word in black_list:
        # And for each line in the subtitle block to analyse
        for line in subtitle_block:
            # If one of the words in the list is found
            if line.find(black_word) != -1:
                # Return the value
                return True

    # If all is good
    return False


# Method to load all words in the black list into a simple word list
def load_words():
    # This one gets the running path. The text file with the words to be removed should be there
    base_path = os.path.dirname(sys.argv[0])
    black_list_path = base_path + "/black_list.txt"

    if not os.path.isfile(black_list_path):
        raise Exception("ERROR: The file " + black_list_path + " doesn't exist!")

    black_list_file = open(black_list_path, "r+")

    black_list = []

    tmp = black_list_file.readline().strip("\n")

    while tmp != "":
        black_list.append(tmp)
        tmp = black_list_file.readline().strip("\n")

    return black_list

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise Exception("ERROR: Wrong number of input arguments")

    cleaner(sys.argv[1], sys.argv[2])