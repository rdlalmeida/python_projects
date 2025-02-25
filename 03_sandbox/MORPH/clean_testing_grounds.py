import os
import ricardo_conf

basepath = "/home/ricardoalmeida/morph"

if os.path.exists(basepath + "/rinex_data"):
	os.system("rm -rf " + basepath + "/rinex_data")

if os.path.exists(basepath + "/test_data_archive"):
	if not os.listdir(basepath + "/test_data_archive") == []:
		os.system("mv " + basepath + "/test_data_archive/* " + basepath + "/test_data/")
	os.system("rm -rf " + basepath + "/test_data_archive")

if os.path.exists(ricardo_conf.zz06_list_of_files):
	os.system("rm -rf " + ricardo_conf.zz06_list_of_files)

if os.path.exists(ricardo_conf.rtk_path):
	os.system("rm -rf " + ricardo_conf.rtk_path)

if os.path.exists(basepath + "/rtk_archive"):
	os.system("rm -rf" + basepath + "/rtk_archive")

if os.path.exists(basepath + "/movement_records"):
	os.system("rm -rf " + basepath + "/movement_records")
