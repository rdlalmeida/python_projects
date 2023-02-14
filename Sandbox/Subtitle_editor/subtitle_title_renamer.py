# This script simply renames the subtitle according to the format <Series name> [<Season>x<Episode>] <Episode name>.srt
# In the process, a text file is reloaded - title_words_to_remove.txt - in which words that need to be removed are
# stored, i.e, crap like HDTV, DVDrip, en, and such
# Invocation example: python subtitle_title_renamer.py "/home/ricardoalmeida/Downloads/Deadwood Season 3" ".mkv" "Deadwood [03x" "S\d\dE\d\d" "1080p,x265,10bit,Tigole"
# IMPORTANT NOTE: The list of tokens to remove passed as argument eventually goes into a regex split function that splits the
# string sent as an argument by splitting words by '.', ',', and '-'. Which means that if any of this characters is in one of the
# words, its going to disappear and the word itself split by it. For example, if "WEB-DL" is passed as a token to remove, down
# the road its going to be processed as "WEB" and "DL", with the actual '-' gone. Please take care with this

# PIECE OF SHIT NOT WORKING FOR 30 ROCK TITLES- DEBUG THE MOTHERFUCKER ASAP

import utils
import os
import configuration
import re
import processor

def subtitle_title_renamer():
    # Lets start by loading the text file with the words to remove
    word_database = open(os.getcwd() + "/title_words_to_remove", "r")

    # And now to get the files to which I want to operate
    subtitle_files = os.listdir(configuration.target_path)
    subtitle_files = list(filter(lambda subtitle_file: subtitle_file[-4:] == ".srt", subtitle_files))
    subtitle_files.sort()

    list_of_words_to_remove = utils.get_words_to_remove_database(word_database)

    for subtitle_file in subtitle_files:
        # Regular expression explanation:
        # r - just something that denotes a regular expression and not a normal string after the quotes
        # findall - get all characters matching the regular expression provided
        # [^ .-] - The ^ element is a negation, which translates to match all elements OTHER THAN the ones inside the
        # square brackets, i.e, the " ", "." and "-"
        # The next expression is equivalent to tokeninze by " ", "." and "-"
        tokens = re.findall(r"[^ .-]+", subtitle_file)

        new_title = ""

        # Now to assemble the new title
        for i in range(0, len(tokens) - 1, 1):
            if tokens[i] in list_of_words_to_remove:
                continue
            else:
                if i == 0 or i == 1:
                    new_title = new_title + tokens[i] + " "
                elif i == 2:
                    new_title = new_title + "[0" + tokens[i] + "] "
                else:
                    new_title = new_title + tokens[i] + " "

        # Remove the extra final space
        new_title = new_title[0:-1]

        new_title = new_title + "." + tokens[len(tokens) - 1]

        print(new_title)

        # Rename the files with the good name
        os.rename(configuration.target_path + "/" + subtitle_file, configuration.target_path + "/" + new_title)

def get_episode_number(episode_name):
    # Split the episode name for tokens, as always
    episode_tokens = re.findall(
        processor.main_regex_spliter,
        episode_name)

    # Go through all of them
    for k in range(0, len(episode_tokens)):
        # Check if the current token matche the regex provided to isolate the episode number
        if (re.match(
                processor.episode_token_regex,
                episode_tokens[k])
        ):
            # Return the isolated episode number, in an int format for easier sorting
            return int(episode_tokens[k])

    # If no valid matches were found, return a None instead
    return None

# And this one does pretty much the same but to the video files
def video_file_renamer(video_files_path, video_extension, main_title, episode_list_format, tokens_to_remove):
    ''' video_files_path = UNIX format path to the folder containing the video files to rename'''
    # First validate the input arguments
    if not os.path.isdir(video_files_path):
        raise Exception("ERROR: The path to the video files provided " + video_files_path + " is invalid!")

    # List all files in the provided path
    video_files = os.listdir(video_files_path)

    if (processor.sort_with_regex):
        video_files.sort(key=get_episode_number)
    else:
        video_files.sort()

    # Filter for just the ones that we want to rename
    video_files = list(filter(lambda video_file: video_file[-4:] == video_extension, video_files))

    # The inputed argument is a string, as it is defaulted. The next line converts it into a list
    tokens_to_remove = tokens_to_remove.split(",")

    # Now go through each one of them
    for i in range(0, len(video_files)):
        # Start by tokenizing the name
        tokens = re.findall(
            processor.main_regex_spliter,
            video_files[i]
        )
        # tokens = re.findall(alt_regex_spliter, video_files[i])

        # Now filter all the good tokens
        clean_tokens = []

        index = 0
        current_token = tokens[index]

        # Now go through all tokens until we find the one that matches the episode separator (S something E something in
        # most cases)
        while not re.match(episode_list_format, current_token):
            # If the current token doesn't match the regex for the episode namer
            index += 1                              # Increment the index
            current_token = tokens[index]           # And update the current token

            if index > len(tokens):
                raise Exception("ERROR: Check the provided episode list regex. There are no matching tokens for the one provided")

        # At this point, my index points to the episode separator. As such I need to move to the next one
        index += 1
        final_title = ""

        # Start building the new title. Note: the main_title string provided should include the season index
        final_title += main_title + processor.get_season_index(i + 1) + "] "
        # final_title += main_title + processor.get_season_index(i + 1) + "] Episode " + str(processor.get_season_index(i + 1))

        # Reset the token list
        tokens = tokens[index:len(tokens)]
        # Now go through the rest of the tokens
        for j in range(0, len(tokens)):
            # If an valid token is found
            if tokens[j] not in tokens_to_remove:
                clean_tokens.append(tokens[j])                    # Add it to the clean list

        # Join all good tokens to the final title, apart from the last one which is the file extension
        for clean_token in clean_tokens[0: -1]:
            final_title += clean_token.strip() + " "

        # for clean_token in clean_tokens:
        #     final_title += clean_token.strip() + " "

        # Remove any extra leading or trailing whitespaces from the previous loop
        final_title = final_title.strip();

        # And finally, join the file extension by removing the last space and replacing it by a "."
        # final_title = final_title[:-1] + "." + clean_tokens[-1]
        final_title = final_title + video_extension

        # With the final title all nice and clean, its now time to rename the files
        #file_renamer_UNIX(video_files_path, video_files[i], final_title)
        file_renamer_WIN(video_files_path, video_files[i], final_title)


def file_renamer_UNIX(path_to_folder, old_name, new_name):
    # Check the input arguments, as always
    if not os.path.isdir(path_to_folder):
        raise Exception("ERROR: The path provided " + path_to_folder + " is not valid.")

    if len(old_name) <= 0:
        raise Exception("ERROR: Invalid 'old name'!")

    if len(new_name) <= 0:
        raise Exception("ERROR: Invalid 'new name'!")

    # First, I need to escape all crazy characters in the names: path and file names
    characters_to_escape = [' ', '(', ')']

    for character_to_escape in characters_to_escape:
        path_to_folder = path_to_folder.replace(character_to_escape, "\\" + character_to_escape)
        old_name = old_name.replace(character_to_escape, "\\" + character_to_escape)
        new_name = new_name.replace(character_to_escape, "\\" + character_to_escape)

    #print path_to_folder
    #print old_name
    #print new_name

    # Rename the file if all is OK
    os.system("mv " + os.path.join(path_to_folder, old_name + " " + os.path.join(path_to_folder, new_name)))
    #os.renames(os.path.join(path_to_folder, old_name), os.path.join(path_to_folder, new_name))
    print("Successfully renamed " + old_name + " to " + new_name + " in " + path_to_folder)

def file_renamer_WIN(path_to_folder, old_name, new_name):
    # Check the input arguments, as always
    if not os.path.isdir(path_to_folder):
        raise Exception("ERROR: The path provided " + path_to_folder + " is not valid.")

    if len(old_name) <= 0:
        raise Exception("ERROR: Invalid 'old name'!")

    if len(new_name) <= 0:
        raise Exception("ERROR: Invalid 'new name'!")

    # First, I need to escape all crazy characters in the names: path and file names
    #characters_to_escape = [' ', '(', ')']

    #for character_to_escape in characters_to_escape:
        #path_to_folder = path_to_folder.replace(character_to_escape, "\\" + character_to_escape)
        #old_name = old_name.replace(character_to_escape, "\\" + character_to_escape)
        #new_name = new_name.replace(character_to_escape, "\\" + character_to_escape)

    #print path_to_folder
    #print old_name
    #print new_name

    # Rename the file if all is OK
    # os.system("mv " + os.path.join(path_to_folder, old_name + " " + os.path.join(path_to_folder, new_name)))
    os.renames(os.path.join(path_to_folder, old_name), os.path.join(path_to_folder, new_name))
    print("Successfully renamed " + old_name + " to " + new_name + " in " + path_to_folder)

if __name__ == "__main__":
    # if len(sys.argv) != 6:
    #     raise Exception("ERROR: Invalid number of arguments!")

    main_title = "The Night Of"
    season_number = 1

    video_files_path = "D:\\Downloads\\FinishedDownloads\\" + main_title + "\\" + main_title + " Season "
    main_title = main_title + " ["
    if (str(season_number).__len__() == 1):
        video_files_path += "0" + str(season_number)
        main_title += "0" + str(season_number) + "x"
    else:
        video_files_path += str(season_number)
        main_title += str(season_number) + "x"

    video_extension = ".mkv"
    episode_list_format = "S\\d\\dE\\d\\d"
    tokens_to_remove = ""

    video_file_renamer(video_files_path, video_extension, main_title, episode_list_format, tokens_to_remove)

    # video_file_renamer(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
