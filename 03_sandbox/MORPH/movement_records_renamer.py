import os
import utils

path = "/home/ricardoalmeida/morph/movement_records"

filelist = os.listdir(path)

for file_to_edit in filelist:

	file_to_edit_path = path + "/" + file_to_edit
	tmp_file_path = path + "/temp_file.csv"

	read_file = open(file_to_edit_path, "r")
	line = read_file.readline().strip("\n")
	temp_file = open(tmp_file_path, "w")

	while line != "":
		#print "Old line: " + line
		tokens = line.split(",")

		tokens[0] = utils.get_current_year() + "_" + (tokens[0])[4:7]
		new_line = ""
		# Reassemble tokens
		for token in tokens:
			new_line = new_line + token + ","

		new_line = new_line[0:-1]
		#print "New line: " + new_line

		temp_file.write(new_line + "\n")

		line = read_file.readline().strip("\n")

	temp_file.close()

	os.system("rm -rf " + file_to_edit_path)
	os.system("mv " + tmp_file_path + " " + file_to_edit_path)