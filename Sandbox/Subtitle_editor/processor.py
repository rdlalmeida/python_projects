import file_title_renamer
import Subtitle_cleaner_WIN
import Subtitle_cleaner_UNIX
import title_swapper

season_counter = 1
main_title = "The Night Of"
target_path = "D:\\Downloads\\FinishedDownloads\\" + main_title + "\\" + main_title + " Season " \
              + ('0' + str(season_counter) if (str(season_counter)).__len__() < 2 else str(season_counter))
video_file_extension = ".mkv"
sub_file_extension = ".srt"
main_title = main_title + " [" + \
             ('0' + str(season_counter) if (str(season_counter)).__len__() < 2 else str(season_counter)) + \
             "x"
episode_token_regex = "S\\d\\dE\\d\\d"
tokens_to_remove = "720p,WEB,DL,HEVC,x265,sharpysword"
main_regex_spliter = r"[^ ._-]+"
# main_regex_spliter = r"[^ ._]+"
alt_regex_spliter = r"[^_-]+"

# Set this flag to indicate that the sorting of video files/subtitle files needs to be done using the episode token regex argument
# Use this for the cases where the filenames have a non-logical numbering, such as 1, 2, 10, 11. When the script tries to sort items using with these elements, the two digit numbers appear before the single digit
# ones, which messes up the
sort_with_regex = False


# Simple function to retrive the season index to add to all sorts of element depending on the number of characters that the current counter has. For example, for season 1, 4, 8, etc.., the season string expected is
# 01, 04, 08 and so on. If the season is the 23rd, for instance, than the relevant string is simply 23
def get_season_index(season_counter):
    counter_str = str(season_counter)

    if (counter_str.__len__() < 2):
        return "0" + counter_str
    else:
        return counter_str


if __name__ == "__main__":
    # Start by cleaning out the subtitle files (make sure the subtitle file extensions is correct)
    try:
        Subtitle_cleaner_WIN.cleaner(target_path, sub_file_extension)
    except Exception as ex:
        print ("Unable to clean subtitles in '" + str(target_path) + "': " + ex.__str__)
        exit(-1)
    else:
        print("All subtitles were cleaned successfully!")

    # Rename the video/subtitle file next
    try:
        subtitle_title_renamer.video_file_renamer(
            video_files_path=target_path,
            video_extension=video_file_extension,
            main_title=main_title,
            episode_list_format=episode_token_regex,
            tokens_to_remove=tokens_to_remove
        )
    except Exception as ex:
        print("Unable to rename '" + video_file_extension + "' files in '" + target_path + "': " + ex.__str__)
        exit(-2)
    else:
        print("All '" + video_file_extension + "' files successfully renamed in '" + target_path + "'.")

    origin = video_file_extension
    destination = sub_file_extension
    # Finally, copy the curated filenames to the respective subtitle files
    try:
        title_swapper.title_swapper_WIN(
            base_path=target_path,
            origin=origin,
            destination=destination,
            episode_list_format=episode_token_regex
        )
    except Exceptio as ex:
        print("Unable to copy filenames from '" + origin + "' to '" + destination + "' files!")
        exit(-3)
    else:
        print("All filenames from'" + origin + "' files copies to the '" + destination + "' successfully!")
