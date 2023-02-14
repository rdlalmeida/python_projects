# This one goes through a subtitle file, line by line, and removes any offending block of lines, i.e, a group of lines
# headed by a sequential line and a time line
# I'm going to get the main parameters through the command line for simplicity of sorts

import os
import sys
import utils

# String used to separate subtitle blocks
#block_separator = '\r\n'
block_separator = '\n'


def cleaner(path_to_dirty_subs, subs_extension):
    """
    Method to clear out stupid commentary blocks from a subtitle file in an autonomous fashion. The trigger words to signal a
    subtitle block for removal are stored in the 'black_list.txt' file. Update it to include whichever
    lines you want to get rid off.
    :param path_to_dirty_subs: Path to the directory housing the sub file with extra "words"
    :param subs_extension: The file extension (in str format) of those files, e. g, '.srt', '.sub', ect..
    :return: Nothing. The method replaces the dirty files for their clean versions
    """
    # Check if the provided path is valid
    if not os.path.isdir(path_to_dirty_subs):
        raise Exception("ERROR: The path provided: " + path_to_dirty_subs + " is invalid!")

    # Check if the extension provided is a valid one in length and in type
    if len(subs_extension) <= 0 or not isinstance(subs_extension, str):
        raise Exception("ERROR: The extension provided: " + subs_extension + " is invalid!")

    sub_files = os.listdir(path_to_dirty_subs)
    sub_files = list(filter(lambda file: file[-len(subs_extension):] == subs_extension, sub_files))

    # Get the list with all the subtitle files to clean
    sub_files.sort()

    utils.print_folder(path_to_dirty_subs, sub_files)

    # And the list with trigger words
    black_list = load_words()

    # Now circle for all the subtitle files
    for i in range(0, len(sub_files)):
        if not os.path.isfile(os.path.join(path_to_dirty_subs, sub_files[i])):
            raise Exception("ERROR: The file" + os.path.join(path_to_dirty_subs, sub_files[i]) + " is invalid!")

        # Open the current file to read
        current_file = open(os.path.join(path_to_dirty_subs, sub_files[i]), mode='r+',encoding='latin-1')
        tmp_file = open(os.path.join(path_to_dirty_subs, "tmp.txt"), "a+")

        # Get the first written line
        current_line = current_file.readline().strip('\n')

        # I'm going to operate on line blocks
        line_block = []

        # So, as it turned out, I'm still getting surprised on how retarded some of the subtitlers are. I got these .srt
        # files for the first season of Boardwalk Empire and by some unknown and strange reason, some of the subtitle files
        # were reporting unencodable characters or they behave weirdly when run through my cleanup program. Specifically, the
        # run was OK in the sense that all offending blocks were correctly removed, but running the program a second time would
        # return and empty (0 byte) subtitle file, i.e, all the text was deleted!
        # After a few hours reading and debugging the thing, I found out that what appeared to be just innocent empty line
        # (when seen in Notepad++) actually contained some weird characters that only python was getting hold of them!
        # So, my program on its first run would remove these weird characters all together and replace them by empty lines (""),
        # On its second run, it would then see those same empty lines in the beginning of the file and assumed that it had
        # finished processing it and thus simply closing the still empty temp text file and renaming it to the original .srt
        # name!
        # This is the type of shit that annoys me to the max! Someone need to be specially retarded to go all the way to
        # insert characters that no one has seen before, not even Notepad++, that are pretty much invisible to most
        # text readers. Anyhow, the solution is actually quite simple: Now, before doing the bulk of my work (that 'while'
        # loop that goes through the whole document one line at a time) I need to 'clean' up the beginning of the document.
        # Because if that shit had put those characters mixed in with the rest of the text, my program is already smart enough
        # to replace them by empty characters and I wouldn't have wasted a whole afternoon hunting bugs. But by doing that right
        # at the start of the document... that shit is evil.

        # Begin by reading the first line of the document and cleaning it up from any weird characters, which in this case is
        # anything outside of the ASCII range (0 < ord(char) < 128)
        current_line = "".join(i for i in current_line if ord(i) < 128)

        # While this read operation at the start of the document comes up empty, either by misplaced newlines at the start
        # or any sort of weird character map that the asians love to do, just keep reading. Nothing would be saved until the
        # first valid line is found
        while current_line == "":
            # Same process as before: read line
            current_line = current_file.readline().strip('\n').strip()
            # And clean it before moving on
            current_line = "".join(i for i in current_line if ord(i) < 128)

        # At this point I should have a nicely formated text file for analysis.
        # Run the loop until the EOF is reached
        while current_line != "":

            if current_line == block_separator:
                # If the line block is valid
                if validate_block(line_block, black_list):
                    # Go through each line
                    for line in line_block:
                        # First clean up any non-ASCII characters in line. Some idiots are too fond of those I'm afraid
                        line = "".join(i for i in line if ord(i) < 128)
                        # And write the line in the temporary file
                        tmp_file.write(line.strip() + "\n")
                    # Add a new line to the end of the subtitle block
                    tmp_file.write("\n")
                    tmp_file.flush()

                    # Reset the line block
                    line_block = []
                else:
                    # If the block comes out as invalid, discard it by resetting the current line block
                    line_block = []
            else:
                # Otherwise just add the current line to the current block and continue
                line_block.append(current_line.strip("\n").strip())

            # Get the next line
            current_line = current_file.readline()

        # Here I got to the end of my file. I'm out of the while loop because I've hit EOF but I still have the last block
        # of the file to process, i.e, either write it or loose it
        if validate_block(line_block, black_list):
            # If the block is valid, then I need to write it to the temp file before closing it
            for line in line_block:
                line = "".join(i for i in line if ord(i) < 128)
                tmp_file.write(line.strip() + "\n")

            tmp_file.write("\n")
            tmp_file.flush()
        else:
            # If its a bad block, than ignore it and move on
            pass

        tmp_file.close()
        current_file.close()

        # And now, remove the original file
        #os.system("rm -rf " + os.path.join(path_to_dirty_subs, sub_files[i].replace(' ', '\ ')))
        os.remove(os.path.join(path_to_dirty_subs, sub_files[i]))

        # And rename the temporary file as the original one
        #os.system("mv " + os.path.join(path_to_dirty_subs, "tmp.txt") + " " + os.path.join(path_to_dirty_subs, sub_files[i].replace(' ', '\ ')))

        os.rename(os.path.join(path_to_dirty_subs, 'tmp.txt'), os.path.join(path_to_dirty_subs, sub_files[i]))


def validate_block(subtitle_block, black_list):
    """
    Method to analyse a subtitle block. Basically go through each line and check if any of the black listed words is
    there. If yes, then return True and go from there. Else return False and proceed accordingly. Easy hun?
    :param subtitle_block: list of strings with all the lines from the current block
    :param black_list: A list of strings that I want to get rid off
    :return: True if none of the black listed strings was found in that block, False otherwise.
    """

    # Go through all words inside the black list
    for black_word in black_list:
        # And for each line in the subtitle block to analyse
        for line in subtitle_block:
            # If one of the words in the list is found
            if line.find(black_word) != -1:
                # Return the value
                return False

    # If all is good
    return True


# Method to load all words in the black list into a simple word list
def load_words():
    # This one gets the running path. The text file with the words to be removed should be there
    base_path = os.path.dirname(sys.argv[0])
    #black_list_path = base_path + "/black_list.txt"
    black_list_path = os.path.join(base_path, 'black_list.txt')

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
    # if len(sys.argv) != 3:
    #     raise Exception("ERROR: Wrong number of input arguments")

    main_title = "The Americans"
    season_number = 6
    subtitle_path = "D:\\Downloads\\FinishedDownloads\\" + main_title + "\\" + main_title + " Season ";
    if (str(season_number).__len__() == 1):
        subtitle_path += "0" + str(season_number)
    else:
        subtitle_path += str(season_number)
    subtitle_extension = ".srt"


    # cleaner(sys.argv[1], sys.argv[2])
    cleaner(subtitle_path, subtitle_extension)