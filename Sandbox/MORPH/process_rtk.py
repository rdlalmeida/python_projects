import os
import sys
from ricardo_conf import *
from utils import *

def get_rtk_processed_files(path, rtk_processed_files):
    files_in_folder = os.listdir(path)

    for file in files_in_folder:
        if os.path.isdir(path + "/" + file):
            get_rtk_processed_files(path + "/" + file, rtk_processed_files)
        else:
            rtk_processed_files.append(file)

    return rtk_processed_files

create_folder_if_necessary(rtk_path)

rtk_processed_files = get_rtk_processed_files(rtk_path, [])
rtk_processed_files.sort()

#Simple function to abstract the filename creation process. The output pattern is
#output_<first_receiver>_<second_receiver>_<.o file day of the year>.csv
def create_output_filename(distance_to_process, rinex_processed_filename):
	return "output_" + distance_to_process[0] + "_" + distance_to_process[1] + "_" + get_day_of_year_date(rinex_processed_filename) + ".csv"

#Another simple function to abstract the rtk processing command (a rather complex one by the way)
def create_rtk_process_command(distance_to_process, rinex_processed_filename):
    return rnx2rtkp_path + " -k " + rtk_config + " " + rinex_path + "/" + distance_to_process[0] + "/" + rinex_processed_filename + " " + rinex_path + "/" + distance_to_process[1] + "/" + rinex_processed_filename + " " + rinex_path + "/" + distance_to_process[0] + "/" + rinex_processed_filename[0:-1] + "n -o " + rtk_path + "/" + create_output_filename(distance_to_process, rinex_processed_filename)

#This function returns the pattern used by the rinex application to generate its file names, using the day
#of the year number with the zero padding
def get_day_of_year_date(rinex_processed_filename):
	return rinex_processed_filename[0:-4]

if __name__ == "__main__":
    if len(sys.argv) > 2:
        s1 = sys.argv[1]
        s2 = sys.argv[2]
        date = sys.argv[3]
        filename = "0" + get_current_year_sufix() + "_" + date + "." + get_current_year_sufix() + "o"
        os.system(rnx2rtkp_path + " -k " + rtk_config + " " + rinex_path + "/" + s1 + "/" + filename + " " + rinex_path + "/" + s2 + "/" + filename + " " + rinex_path + "/" + s1 + "/" + filename[0:-1] + "n -o " + rtk_path + "/output" + s1 + "_" + s2 + "_" + filename + ".csv")
    else:
        i = 0

        for useful_distance in useful_distances:
            inverted_useful_distance = [useful_distance[1], useful_distance[0]]

#            print "Iteration #", i, " Useful distance = ", useful_distance, " Inverted useful distance = ", inverted_useful_distance
#            i = i + 1
            distances_to_process = [useful_distance, inverted_useful_distance]
            for distance_to_process in distances_to_process:

                #Get all .o and .n files for the site in process
                rinex_processed_files = os.listdir(rinex_path + "/" + distance_to_process[0])
                rinex_processed_files.sort()
                rinex_processed_files = filter(lambda files: "." + get_current_year_sufix() + "o" in files, rinex_processed_files)

                rover_processed_files = os.listdir(rinex_path + "/" + distance_to_process[1])
                rover_processed_files.sort()
                rover_processed_files = filter(lambda files: "." + get_current_year_sufix() + "o" in files, rover_processed_files)

                for rinex_processed_file in rinex_processed_files:
                    if rinex_processed_file in rover_processed_files:

                        output_filename = create_output_filename(distance_to_process, rinex_processed_file)

                        if output_filename not in rtk_processed_files:

                            print "Processing ", distance_to_process, "(", str(i * 2 + distances_to_process.index(distance_to_process) + 1) + "/" + str(len(useful_distances) * 2), ")"

                            print create_rtk_process_command(distance_to_process, rinex_processed_file)
                            os.system(create_rtk_process_command(distance_to_process, rinex_processed_file))

                            dest_path = rtk_path + "/" + get_day_of_year_date(rinex_processed_file)

                            if not os.path.exists(dest_path) or not os.path.isdir(dest_path):
                                os.mkdir(dest_path)

                            os.system("mv " + rtk_path + "/" + output_filename + " " + dest_path)

                        else:
                            pass
            i = i + 1

        for site in sites:
            rinex_processed_files = os.listdir(rinex_path + "/" + site)
            rinex_processed_files.sort()
            rinex_processed_files = filter(lambda files: "." + get_current_year_sufix() + "o" in files or "." + get_current_year_sufix() + "n" in files or "." + get_current_year_sufix() + "h" in files, rinex_processed_files)

            for rinex_processed_file in rinex_processed_files:
                if not os.path.isdir(rinex_path + "/" + site + "/Completed"):
                    os.system("mkdir " + rinex_path + "/" + site + "/Completed")
                    print rinex_path + "/" + site + "/Completed folder created"

                if not os.path.isdir(rinex_path + "/" + rinex_processed_file):
                    os.system("mv " + rinex_path + "/" + site + "/" + rinex_processed_file + " " + rinex_path + "/" + site + "/Completed/")
                    print "File ", rinex_processed_file, " moved to ", rinex_path + "/" + site + "/Completed"