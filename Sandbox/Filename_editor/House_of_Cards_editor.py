import os
import sys

base_path = "/media/ricardoalmeida/Data/Series"
temp_file_path = os.path.join(base_path,"temp_sub.srt")

files = os.listdir(base_path)


def print_elems(elem_list):
    for elem in elem_list:
        print(elem)

videos = []
subs = []

videos = filter(lambda file: file[-3:] == "mkv", files)
videos.sort()

subs = filter(lambda file: file[-3:] == "srt", files)
subs.sort()

#print "Videos:"
#print_elems(videos)

#print "Subs:"
#print_elems(subs)


def rename_videos(videos):
    for i in range(0, len(videos)):
        tokens = videos[i].split(" ")

        new_title = " ".join(tokens[0:3])
        new_title += " [" + tokens[4][1:3] + "x" + tokens[4][4:6] + "] Chapter " + str(int(tokens[4][4:6]) + 39) + tokens[4][-4:]

        print("Renaming " + os.path.join(base_path.replace(" ", "\ "), videos[i].replace(" ", "\ ")) + " to " + \
              os.path.join(base_path.replace(" ", "\ "), new_title.replace(" ", "\ ")) + ":")
        os.system("mv " + os.path.join(base_path.replace(" ", "\ "), videos[i].replace(" ", "\ ")) +
                  " " + os.path.join(base_path.replace(" ", "\ "), new_title.replace(" ", "\ ")))


def rename_subs(videos, subs, base_path):
    videos.sort()
    subs.sort()
    base_path = base_path.replace(" ", "\ ")

    for i in range(0, len(videos)):
        new_sub_title = videos[i].replace(videos[i][-3:], subs[i][-3:])
        proper_sub = subs[i].replace(" ", "\ ")
        new_sub_title = new_sub_title.replace(" ", "\ ")

        print("Replacing " + os.path.join(base_path, proper_sub) + " for " + os.path.join(base_path, new_sub_title))
        os.system("mv " + os.path.join(base_path, proper_sub) + " " + os.path.join(base_path, new_sub_title))


def subtitle_cleaner(base_path, sub_file, temp_file_path):
    sub_to_clean = open(os.path.join(base_path, sub_file), "r")
    temp_file = open(temp_file_path, "w+")

    dirname, filename = os.path.split(os.path.abspath(__file__))
    trigger_words_file = open(os.path.join(dirname, "line_triggers"), "r")
    trigger_words = []

    line = trigger_words_file.readline()

    while line != "":
        line = line.strip()
        if len(line) > 0:
            trigger_words.append(line)
        line = trigger_words_file.readline()

    line = sub_to_clean.readline()
    line = "1"
    line_block = []
    block_counter = 1

    while line != "":
        # Isolated block of subs
        if len(line) == 2:

            flag = False

            print("For #1")
            for i in range(2, len(line_block)):
                for trigger_word in trigger_words:
                    if line_block[i].__contains__(trigger_word):
                        print("Found trigger word " + trigger_word + " in ")
                        for b in line_block:
                            print(b)
                        print("From " + sub_file + "\n")
                        flag = True

            #print "For #2"
            #for l in line_block:
            #    print l[0]
            #    print l[-1]
            #    print str(len(l))
            #    if len(l) > 0 and l[0] == "[" and l[-1] == "]":
            #        print "Removing " + l + " from " + sub_file
            #        line_block.remove(l)

            #print "If #3"
            #if len(line_block) <= 2:
            #    print "This block: "
            #    for lb in line_block:
            #        print lb
            #    print "\nIs virtually empty. Skipping..."
            #    flag = True

            if not flag:
                temp_file.write(str(block_counter) + "\n")
                block_counter += 1

                for i in range(1, len(line_block)):
                    temp_file.write(line_block[i] + "\n")
                temp_file.write("\n")

            line_block = []
        else:
            line = line.strip("\n")
            line_block.append(line)

        line = sub_to_clean.readline()

    sub_to_clean.close()
    temp_file.close()

    os.system("rm -rf " + os.path.join(base_path, sub_file).replace(" ", "\ "))
    os.system("mv " + temp_file_path.replace(" ", "\ ") + " " + os.path.join(base_path, sub_file).replace(" ", "\ "))


#subtitle_cleaner(base_path, subs[3], temp_file_path)
#exit(0)


for sub in subs:
    subtitle_cleaner(base_path, sub, temp_file_path)
    print("Fixed " + sub)

#rename_videos(videos)
#rename_subs(videos, subs, base_path)

