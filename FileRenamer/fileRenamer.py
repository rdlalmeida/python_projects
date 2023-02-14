import os
import re
import FileRenamer.utils as utils

#base_path = "D:\Series\Orange is the New Black Season 3"
#base_path = "/home/ricardoalmeida/TMP/temp_subs"

# Simple function to remove unwanted elements from the filename
def cleanupName(filename):

    #First, split the filename by their existing spaces and extension dot
    tokens = re.findall(r"[^ .]+", filename)

    newName = ""

    #Go through all the extracted tokens
    for i in range(tokens.__len__() - 1):
        #And count only the title and sequence number
        if re.search(r"atman", tokens[i]) or re.match(r"\d\d\d", tokens[i]):
            #Concatenate the token to the new name if so
            newName = newName + tokens[i].capitalize() + " "
        else:
            #Otherwise, just don't do anything
            {}

    #Strip any trailing or leading spaces
    newName = newName.strip();

    #And add the file extension at the end
    newName = newName + '.' + tokens[tokens.__len__() - 1]

    return newName

def renameBatman():
    #The path to the working directory
    #myPath = '/home/ricardoalmeida/comics'
    myPath = '/media/ricardoalmeida/Data/Applications/Data/Complete/Batman v1 (001-713+Extras)(1940-2011)/Extras'

    #List all elements in the folder pointed by the path element
    filenames = os.listdir(myPath)

    for f in filenames:
        if os.path.isdir((myPath + '/' + f)):
            filenames.remove(f)

    #Sort them alphabetically
    filenames = sorted(filenames)

    #Now go through the folder
    for f in filenames:
        #Get a clean filename
        newName = cleanupName(f)

        #And rename it
        #os.rename(myPath + '/' + f, myPath + '/' + newName)
        print ("Old name: {0} \nNew name: {1}\n".format(f, newName))

def renameGrooveArmada():
    path = '/media/ricardoalmeida/Data/Applications/Data/Complete/Groove Armada/Compilations/VA - Groove Armada Presents Lovebox (Festivals And Fiestas) - (2008)/CD2'

    filenames = sorted(os.listdir(path))

    for f in filenames:
        #newName = f.replace('Groove Armada ', '')
        #print ("Old name: {0}\nNew name: {1}\n".format(f, newName))

        tokens = re.findall(r"[^ ]+", f)

        #tokens[0] = tokens[0].replace('(', '').replace(')', '')

        if int(tokens[0]) < 10:
            newName = '0' + int(tokens[0]).__str__() + ' - '
        else:
            newName = tokens[0] + ' - '

        for i in range(1, tokens.__len__()):
            newName = newName + tokens[i] + ' '

        newName = newName.strip()

        newName = newName.replace(' _ ', ' - ')

        print ("Old name: {0}\nNew name: {1}\n".format(f, newName))

        os.rename(path + '/' + f, path + '/' + newName)

def rename1():
    path = '/media/ricardoalmeida/Data/Applications/Data/Complete/Zero 7/When it Falls (2004)'

    foldernames = os.listdir(path)

    notCap = ['in', 'the', 'for', 'a', 'of',  'an', 'it', 'our']

    for f in range(0, foldernames.__len__()):
        tokens = re.findall(r"[^ _]+", foldernames[f])

        newName = tokens[0] + ' '

        for i in range(1, tokens.__len__()):
            if i != 2:

                    flag = True

                    for n in notCap:
                        if tokens[i] == n:
                            flag = False

                    if flag:
                        newName = newName + tokens[i].capitalize() + ' '
                    else:
                        newName = newName + tokens[i] + ' '
            else:
                newName = newName + tokens[i].capitalize() + ' '

        newName = newName.strip()

        print ("Old name: {0}\nNew Name: {1}\n".format(foldernames[f], newName))

        print

        os.rename(path + '/' + foldernames[f], path + '/' + newName)

def rename2():
    path = '/media/ricardoalmeida/Data/Applications/Data/Complete/Trentemoller/Compilations/The Polar Mix (2007)/CD2'

    files = os.listdir(path)

    for f in files:

        tokens = re.findall(r"[^ .]+", f)

        if int(tokens[0] < 10):
            newName = '0' + str(int(tokens[0])) + ' - '
        else:
            newName = tokens[0] + ' - '

        for i in range(1, tokens.__len__() - 1):
            newName = newName + tokens[i] + ' '

        newName = newName.strip()

        newName = newName + '.' + tokens[tokens.__len__() - 1]

        newName = newName.replace('_', ' inch')

        print ("Old Name: {0}\nNew Name: {1}\n".format(f, newName))

        os.rename(path + '/' + f, path + '/' + newName)

def remixes():
    path = '/media/ricardoalmeida/Data/Applications/Data/Complete/Trentemoller/Remixes'

    files = os.listdir(path)

    for i in range(0, files.__len__()):
        if i < 9:
            newName = '0' + str(i + 1) + ' - ' + files[i]
        else:
            newName = str(i + 1) + ' - ' + files[i]

        print (newName)

        os.rename(path + '/' + files[i], path + '/' + newName)

def renameFolders(basePath):

    foldernames = os.listdir(basePath)

    newNames = []

    for folder in foldernames:
        tokens = re.findall(r"[^ ]+", folder)

        newName = ''

        for i in range (3, tokens.__len__()):
            newName = newName + tokens[i] + ' '

        newName = newName.strip()

        #newName = newName + '(' + tokens[0] + ')'

        print ("Old name: {0}\nNew Name: {1}\n".format(folder, newName))

        os.rename(basePath + '/' + folder, basePath + '/' + newName)

        #newNames.append(newName)

        newNames.append(folder)
        #newNames.append(folder)
    return newNames



def renameFiles(basePath, folders):

    for p in range(0, folders.__len__()):

        path = basePath + '/' + folders[p]

        files = os.listdir(path)

        for f in files:

            if not os.path.isfile(path + '/' + f):
                fol = []
                fol.append(f)
                renameFiles(path, fol)
            else:
                {}

            tokens = re.findall(r"[^ -]+" ,f)

            for t in tokens:
                tokens[0] = tokens[0].replace('.', '')

                newName = tokens[0] + ' - '

                for i in range(1, tokens.__len__()):
                    newName += tokens[i] + ' '

            newName = newName.strip()

            print ("Old Name: {0}\nNew Name: {1}\n".format(f, newName))

            os.rename(path + '/' + f, path + '/' + newName)

def renameJohnOliver(base_path):
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise Exception("ERROR: The path provided: " + base_path + " is invalid!")

    filelist = os.listdir(base_path)
    filelist.sort()

    for i in range(0, len(filelist)):
        old_name = filelist[i]
        filelist[i] = re.sub(r"-\ss\d\de", "[04x", filelist[i])
        filelist[i] = re.sub(r"\s-", "]", filelist[i])
        new_name = filelist[i]

        os.system("mv " + utils.escape_filename(os.path.join(base_path, old_name)) + " " + utils.escape_filename(os.path.join(base_path, new_name)))

def renameAgents(base_path):
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise Exception("ERROR: The path provided: " + base_path + " is invalid!")

    filelist = os.listdir(base_path)
    filelist.sort()

    for i in range(0, len(filelist)):
        old_name = filelist[i]

        filelist[i] = re.sub(r"S\d\d", "[04x", filelist[i])
        if i < 9:
            filelist[i] = re.sub(r"E\d\d", "0" + str(i + 1) + "]", filelist[i])
        else:
            filelist[i] = re.sub(r"E\d\d", str(i + 1) + "]", filelist[i])

        new_name = filelist[i]

        os.system("mv " + utils.escape_filename(os.path.join(base_path, old_name)) + " " + utils.escape_filename(os.path.join(base_path, new_name)))

# A simple method to rename all files from all 9 seasons of How I Met Your Mother with all the extra "bits" removed, i.e, normalizing the filename to the adopted rule for 10 years now
def rename_mother(base_path):

    if not os.path.isdir(base_path):
        raise Exception("ERROR: Invalid start directory: " + base_path)

    list_of_files = os.listdir(base_path)
    list_of_files.sort()

    for filename in list_of_files:
        # If there are sub folder to base path, then call this function recursively
        if os.path.isdir(os.path.join(base_path, filename)):
            rename_mother(os.path.join(base_path, filename))

        # Otherwise process each file accordingly
        else:
            tokens = re.findall(r"[^ ]+", filename)

            series_title = " ".join(tokens[0:5])

            index = re.search(r'S\d\dE\d\d', filename).group()

            index = index.replace("S", "[").replace("E", "x").__add__("]")

            episode_title = " ".join(tokens[6:len(tokens) - 3]) + tokens[-1][-4:]

            final_title = ' '.join([series_title, index, episode_title])

            # Now lets write stuff
            old_path = os.path.join(base_path, filename)
            new_path = os.path.join(base_path, final_title)

            os.rename(old_path, new_path)

def rename_orange(base_path):
    if not os.path.isdir(base_path):
        raise Exception("ERROR: Invalid base path: {0}".format(str(base_path)))

    list_of_files = os.listdir(base_path)
    sorted(list_of_files)

    video_files = list(filter(lambda f: f[-4:] == '.mkv', list_of_files))
    sub_files = list(filter(lambda f: f[-4:] == '.srt', list_of_files))

    print(str(len(video_files)))
    print(str(len(sub_files)))

    if len(sub_files) != len(video_files):
        raise Exception("ERROR: Mismatch between number of sub and video files")

    for i in range(0, len(video_files)):
        base_name = video_files[i][:-4]
        base_name += sub_files[i][-4:]

        os.rename(os.path.join(base_path, sub_files[i]), os.path.join(base_path, base_name))

def rename30Rock (base_path):
    if not os.path.isdir(base_path):
        raise Exception("The provided base path \"" + str(base_path) + "\" its not a valid folder.")

    list_of_files = os.listdir(base_path)
    video_ext = [".mkv", ".avi", ".mp4"]
    subs_ext = [".srt", ".sub", ".txt"]

    video_files = []
    sub_files = []

    for item in list_of_files:
        if item[-4:] in video_ext:
            video_files.append(item)
        elif item[-4:] in subs_ext:
            sub_files.append(item)
        else:
            raise Exception("The file \"" + str(item) + "\" doesn't have a recognizable extension.")

        # Clean up video files names

        for vid in video_files:
            tokens = re.split

            print("OK")


    exit(0)

base_path = "D:/Downloads/FinishedDownloads/30 Rock/Season 1"

if __name__ == "__main__":
    rename30Rock(base_path)