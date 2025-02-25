import os

src_folder = "D:\Series\PT_Subs"
dst_folder = "D:\Series\EN_Subs"

if __name__ == "__main__":

    os.chdir(dst_folder)

    src_filelist = os.listdir(src_folder)
    src_filelist.sort(reverse=False)

    dst_filelist = os.listdir(dst_folder)
    dst_filelist.sort(reverse=False)

    if len(src_filelist) != len(dst_filelist):
        raise Exception("ERROR: Subtitles folder have different number of files in it.")

    for i in range(0, len(src_filelist)):
        os.rename(os.path.join(dst_folder, dst_filelist[i]), src_filelist[i])


    print ("SUCCESS!!")