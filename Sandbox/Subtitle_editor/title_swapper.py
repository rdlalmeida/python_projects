# This script receives two arguments [ORIGIN] [DESTIN] that should match the file extensions of two different types of files
# What this script then does it simply escapes and copies the filenames from [ORIGIN] to [DESTIN] according to whatever natural
# order they are in
# EXAMPLE: title_swapper.py "D:\Downloads\FinishedDownloads\Friday Night Lights\Friday Night Lights Season 1" ".srt" ".avi"
import os
import utils
import file_title_renamer
import processor


def title_swapper_UNIX(base_path, origin, destination):
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise Exception("ERROR: The base path provided: " + base_path + " is invalid.")

    try:
        origin = str(origin)
    except ValueError:
        raise Exception("ERROR: Wrong type inserted in [ORIGIN]")

    try:
        destination = str(destination)
    except ValueError:
        raise Exception("ERROR: Wrong type inserted in [DESTIN]")

    # After all the same old verifications, lets begin by listing every file in the path provided
    filelist = os.listdir(base_path)

    origin_files = filter(lambda of: of[-len(origin):] == origin, filelist)
    origin_files.sort()

    destination_files = filter(lambda df: df[-len(destination):] == destination, filelist)
    destination_files.sort()

    if len(origin_files) != len(destination_files):
        raise Exception("ERROR: The [ORIGIN] and [DESTIN] files don't match in number!")

    print("Origin: " + origin + "\tDestination: " + destination)

    # Before anything else I have to replace the origin's extension by the destination extension otherwise it is going to change the type of file and create all sorts of problems
    for i in range(0, len(origin_files)):
        origin_files[i] = origin_files[i].replace(origin, destination)

    # All that crap above was just to create to independent and sorted lists with the files to be copied from one side to the other.
    # So, lets just do that then
    for i in range(0, len(origin_files)):
        print("Moving " + utils.escape_filename(origin_files[i]) + " to " + utils.escape_filename(destination_files[i]))
        os.system("mv " + utils.escape_filename(os.path.join(base_path, destination_files[i])) + " " + utils.escape_filename(os.path.join(base_path, origin_files[i])))


def title_swapper_WIN(base_path, origin, destination, episode_list_format=""):
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise Exception("ERROR: The base path provided: " + base_path + " is invalid.")

    try:
        origin = str(origin)
    except ValueError:
        raise Exception("ERROR: Wrong type inserted in [ORIGIN]")

    try:
        destination = str(destination)
    except ValueError:
        raise Exception("ERROR: Wrong type inserted in [DESTIN]")

    # After all the same old verifications, lets begin by listing every file in the path provided
    filelist = os.listdir(base_path)

    origin_files = list(filter(lambda of: of[-len(origin):] == origin, filelist))

    # If an episode number regex was provided, apply the custom sorting function
    if (processor.sort_with_regex):
        origin_files.sort(
            key=subtitle_title_renamer.get_episode_number
        )
    else:
        # Otherwise do a normal sort
        origin_files.sort()

    destination_files = list(filter(lambda df: df[-len(destination):] == destination, filelist))

    if (processor.sort_with_regex):
        destination_files.sort(
            key=subtitle_title_renamer.get_episode_number
        )
    else:
        destination_files.sort()

    if len(origin_files) != len(destination_files):
        raise Exception("ERROR: The [ORIGIN] and [DESTIN] files don't match in number!")

    print("Origin: " + origin + "\tDestination: " + destination)

    # Before anything else I have to replace the origin's extension by the destination extension otherwise it is going to change the type of file and create all sorts of problems
    for i in range(0, len(origin_files)):
        origin_files[i] = origin_files[i].replace(origin, destination)

    # All that crap above was just to create to independent and sorted lists with the files to be copied from one side to the other.
    # So, lets just do that then
    for i in range(0, len(origin_files)):
        print("Moving " + utils.escape_filename(origin_files[i]) + " to " + utils.escape_filename(destination_files[i]))
        #os.system("mv " + utils.escape_filename(os.path.join(base_path, destination_files[i])) + " " + utils.escape_filename(os.path.join(base_path, origin_files[i])))
        os.renames(os.path.join(base_path, destination_files[i]), os.path.join(base_path, origin_files[i]))


if __name__ == "__main__":
    # if len(sys.argv) != 4:
    #     raise Exception("ERROR: Wrong number of input arguments. USAGE: title_swapper.py [PATH_TO_FOLDER] [ORIGIN EXTENSION] [DESTINATION EXTENSION]")

    main_title = "Silicon Valley"
    season_number = 2
    # title_swapper_WIN(sys.argv[1], sys.argv[2], sys.argv[3])
    base_path = "D:\\Downloads\\FinishedDownloads\\" + main_title + "\\" + main_title + " Season "
    # base_path = "D:\\Series\\" + main_title + "\\" + main_title + " Season "
    if (str(season_number).__len__() == 1):
        base_path += "0" + str(season_number)
    else:
        base_path += str(season_number)

    origin = ".mkv"
    destin = ".srt"
    # episode_list_format = "S\\d\\dE\\d\\d"
    episode_list_format = ""
    # base_path = cfg.base_path
    # base_path = sys.argv[1]
    # origin = sys.argv[2]
    # destin = sys.argv[3]

    title_swapper_WIN(base_path=base_path, origin=origin, destination=destin, episode_list_format=episode_list_format)
