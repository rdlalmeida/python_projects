import os
import datetime
import ricardo_conf

print "Start time: ", datetime.datetime.now()


def run(script_name):
	os.system("python " + ricardo_conf.scripts_path + "/" + script_name)

run("update_ZZ06_input_directory.py")
run("process_files.py")
run("process_zz06_files.py")
run("process_rtk.py")
run("process_movement.py")
