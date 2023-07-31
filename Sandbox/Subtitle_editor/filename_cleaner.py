import os
import re
import processor
import file_title_renamer


def cleanup_filename(files_path, file_extension, tokens_to_remove):
    if not os.path.isdir(files_path):
        raise Exception("ERROR: The path to the video files provided '" + files_path + "' is invalid!")

    files_to_clean_list = os.listdir(files_path)

    files_to_clean_list = list(filter(lambda file_to_clean: file_to_clean[-4:] == file_extension, files_to_clean_list))

    for i in range(0, len(files_to_clean_list)):
        filename_tokens = re.findall(
            processor.main_regex_spliter,
            files_to_clean_list[i]
        )

        clean_tokens = []

        final_title = ""

        for j in range(0, len(filename_tokens) - 1):
            if filename_tokens[j] in tokens_to_remove:
                continue
            else:
                final_title += filename_tokens[j] + " "

        final_title = final_title.strip();

        final_title += "." + filename_tokens[-1]

        subtitle_title_renamer.file_renamer_WIN(files_path, files_to_clean_list[i], final_title)


if __name__ == "__main__":
    main_title = "Agents of S.H.I.E.L.D"
    season_numbers = [1]
    files_extension = ".mkv"
    tokens_to_remove = ["1080p", "10bit", "BluRay", "AAC5", "1", "HEVC", "Vyndros"]

    for season_number in season_numbers:
        files_path = "D:\\Downloads\\FinishedDownloads\\" + main_title + "\\" + main_title + " Season 0" + str(season_number)

        cleanup_filename(files_path=files_path, file_extension=files_extension, tokens_to_remove=tokens_to_remove)