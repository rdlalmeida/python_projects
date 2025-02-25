import os
import math
from ricardo_conf import *
import utils
import re


# Check if the support folders exists and create them if not
utils.create_folder_if_necessary(output_path)
utils.create_folder_if_necessary(rtk_archive_path)

unprocessed_dates = os.listdir(rtk_path)
unprocessed_dates = filter(lambda date: date != "Completed", unprocessed_dates)
unprocessed_dates.sort()


for unprocessed_date in unprocessed_dates:
	i = 0
	print "\nProcessing date: " + unprocessed_date

	input_files_to_process = os.listdir(rtk_path + "/" + unprocessed_date)
	input_files_to_process.sort()

	for input_file_name in input_files_to_process:

		tokens = input_file_name.split("_")
		tokens = filter(lambda token: token[0] == "S" or (token[0] == "Z" and token[1] == "Z"), tokens)

		if len(tokens) != 2:
			raise Exception("Input filename incorrect: " + input_file_name)

		useful_distance = [tokens[0], tokens[1]]

		print "Distance #", i, ": ", useful_distance
		i += 1

		output_file_path = output_path + "/movement_" + useful_distance[0] + "_" + useful_distance[1] + ".csv"
		# Check for output file existence
		processed_days = []
		if os.path.exists(output_file_path):
			if not os.path.isfile(output_file_path):
				raise Exception ("The file " + output_file_path + " is not a workable file!")
			else:
				output_file = open(output_file_path, "r")
				for line in output_file.readlines():
					date = line.split(",")[0]
					if re.search(r'.\d\do', date):
						processed_days.append(date[0:-4])
					else:
						processed_days.append(date)

		input_file_path = rtk_path + "/" + unprocessed_date + "/" + input_file_name

		if unprocessed_date in processed_days:
			print "Day ", unprocessed_date, " already processed. Skipping..."
			continue

		output_file = open(output_file_path, "a")               # 'a' is for append
		input_file = open(input_file_path, "r")

		input_lines = input_file.readlines();
		input_lines = filter(lambda line: line[0] != "%", input_lines)
		input_file.close()

		x_offset = 0
		y_offset = 0
		z_offset = 0
		readings = 0
		fails = 0

		for input_line in input_lines:
			tokens = filter(lambda token: token != '' and token != ' ', input_line.split(" "))

			sde = float(tokens[7])
			sdn = float(tokens[8])
			sdu = float(tokens[9])
			ratio = float(tokens[-1])

			e_baseline = float(tokens[2])
			n_baseline = float(tokens[3])
			u_baseline = float(tokens[4])

			if sde < 0.01 and sdn < 0.01 and sdu < 0.05 and ratio > 10:
				x_offset += e_baseline
				y_offset += n_baseline
				z_offset += u_baseline
				readings += 1
			else:
				fails += 1

		try:
			average_distance = math.sqrt((x_offset/readings)**2 + (y_offset/readings)**2 + (z_offset/readings)**2)

			print unprocessed_date, " ", (x_offset/readings), " ", (y_offset/readings), " ", (z_offset/readings), " " \
			, average_distance, " ", str((readings)*100/(readings + fails)), "%"

			if float(1.0*readings/(1.0*(readings + fails))) > 0.01:
				output_file.write(unprocessed_date + "," + str(x_offset/readings) + "," + str(y_offset/readings) + "," + str(z_offset/readings) + "," + str(average_distance) + "\n")
			else:
				output_file.write(unprocessed_date + ",INVALID\n")
				print "Discarding data-set"
		except ZeroDivisionError:
			output_file.write(unprocessed_date + ",INVALID\n")
			print "No valid data for date ", unprocessed_date

		output_file.close()

		complete_date_folder = rtk_archive_path + "/" + unprocessed_date

		utils.create_folder_if_necessary(complete_date_folder)

		os.system("mv " + input_file_path + " " + complete_date_folder)
		print "File " + input_file.name + " moved to " + complete_date_folder

		if len(os.listdir(rtk_path + "/" + unprocessed_date)) == 0:
			os.system("rm -rf " + rtk_path + "/" + unprocessed_date)
			print "Deleted " + rtk_path + "/" + unprocessed_date
