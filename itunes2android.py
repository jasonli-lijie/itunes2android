from iTunesXmlParser import *
import sys
import urllib
import os
import string
import codecs
import getopt
import pickle

###########################################
# m4v is ok
# mp4 has some issue? will check
#
###########################################
#global variables
android_media_folder_path = '''/sdcard/AndroidMusic/'''
temp_filename_to_be_deleted = 'itunes2android.tmp'
command_list_file='''commands.bat'''
g_playlist_list = []
g_album_list = []
g_artist_list = []

g_playlist_set = set()
g_album_set = set()
g_artist_set = set()
g_last_option_filename = '''last_options.dat'''

###########################################################################
# To get filename from a complete path
# Input: 
#    song
#    the string which has all songs names
#
###########################################################################
def get_filename_from_location_path(complete_location_path):
	location_path_array = complete_location_path.split('\\')
#	print 'filename to check is ', location_path_array[len(location_path_array)-1]
	return location_path_array[len(location_path_array)-1]
	
###########################################################################
# To check if the song has been included on the devices already
# Input: 
#    song
#    the string which has all songs names
#
###########################################################################
def is_new_song_for_device(song, file_list_already_on_device):
	local_pathname = urllib.url2pathname(song.location.replace('file://localhost/','///'))
	if file_list_already_on_device.find(get_filename_from_location_path(local_pathname).strip()) == -1:
#		print 'cannot find ', local_pathname, 'from the device'
		return True
	else:
#		print "This file is already on the device " + urllib.url2pathname(song.location.replace('file://localhost/','///'))
		return False
		
###########################################################################
# To check if the song should be synchronized
# Input: 
#    song
#    track_id_set: the list of track id in the playlist
#
###########################################################################
def check_if_song_to_be_synchronizaed(song, track_id_set):
#	if song.location.endswith('mp3') or song.location.endswith('mp4'):
#	if song.location.endswith('mp3'):
	if song.track_id in track_id_set or song.album in g_album_set or song.artist in g_artist_set:
		return True
	else:
#		print "Will not be copied! " + urllib.url2pathname(song.location.replace('file://localhost/','///'))
		return False

###########################################################################
# To get the android platform version
# Read it from file /system/build.prop
# Stupid Android 1.6: without grep in the sandbox, 
# so I have to handle the build.prop file myself
###########################################################################
def get_android_version():
	global temp_filename_to_be_deleted
	command_line = 'adb shell cat /system/build.prop > ' + temp_filename_to_be_deleted
	os.system(command_line)
	android_version = ''
	try:
		report_file = open(temp_filename_to_be_deleted,"r")
	except IOError, message:
		print >> sys.stderr, "cannot copy build prop file to local: ", message
		sys.exit(1)
	#something may wrong here because this file could be 3 lines if adb daemon has not been started yet
	report_lines = report_file.readlines()
	for line in report_lines:
		if line.startswith('ro.build.version.release'): # got you
			words_in_line = line.split('=')
			android_version = words_in_line[1]
			android_version_number = android_version.split('-')
	report_file.close()
	return android_version

###########################################################################
#parse the report file
#sample report file (case 1: Android 1.6 or earlier):
# /sdcard: 989980K total, 12712K used, 977268K available (block size 4096)
#sample report file (case 2: Android 2.0 or later):
# Filesystem           1K-blocks      Used Available Use% Mounted on
#
#/dev/block//vold/179:1
#
#                        990944    182664    808280  18% /sdcard
#----------------------------------------------------------------------
# We can get Android version from this file:
# /system/build.prop
# field is ro.build.version.release
###########################################################################
def get_free_space_on_device():
	global temp_filename_to_be_deleted
	free_space_bytes = 0
	disk_usage_report = temp_filename_to_be_deleted
	android_version = get_android_version()
	command_line = 'adb shell df /sdcard > ' + disk_usage_report
	os.system(command_line)
#	print 'Android version is', android_version
#######1.6 or ealier check:	
	try:
		report_file = open(disk_usage_report,"r")
	except IOError, message:
		print >> sys.stderr, "ADB result file could not be opened: ", message
		sys.exit(1)
	#something may wrong here because this file could be 3 lines if adb daemon has not been started yet
	all_in_one_line = report_file.read().strip()
	if all_in_one_line.startswith('Filesystem'):
		android_version = '2.x'  #stupid workaround for Motorola XT800 because I don't want to change the code strucuture a lot!
	if all_in_one_line.startswith('/sdcard'):
		android_version = '1.x'  #stupid workaround for Motorola XT800 because I don't want to change the code strucuture a lot!
	
	report_lines = all_in_one_line.split('\n')
	print android_version
	print report_lines

	if android_version.startswith('1.'):
		first_line = ''
		for line in report_lines:
			if line.startswith('/sdcard:'):
				first_line = line
				break
		if first_line.startswith('/sdcard:'): #correct format
			words_array_in_first_line = first_line.split()
			#words_array_in_first_line[5] is the string for available space
			temp_array = words_array_in_first_line[5].split('K')
			has_a_k = False
			if len(temp_array) == 2: #has a K
				has_a_k = True
			available_space_string = temp_array[0] #anyway we can get the digits here		
			if available_space_string.isdigit():
				free_space_bytes = string.atoi(available_space_string)
				if has_a_k:
					free_space_bytes = free_space_bytes * 1024
			else: #something must be wrong
				print >> sys.stderr, "cannot check the free space of the SD card!!!"
				sys.exit(1)
		else: #something wrong with the report file
			print >> sys.stderr, "ADB result file format error, I cannot understand."
			sys.exit(1)
	else: #Android 2.0 or later
# Filesystem           1K-blocks      Used Available Use% Mounted on
#
#/dev/block//vold/179:1
#
#                        990944    182664    808280  18% /sdcard
#		print 'I am in Android 2.0 or above'
		target_line = ''
		for line in report_lines:
#			print 'to check line: ', line
			if line.find('/sdcard') > -1:
				target_line = line
				break
#		print 'target_line: ', target_line
		words_array_in_target_line = target_line.split()
		#should be words_array_in_target_line[2], and it should be measured by K
		print words_array_in_target_line
		free_space_bytes_string = words_array_in_target_line[2]
#		print 'Number could be ', free_space_bytes_string
		free_space_bytes = string.atoi(free_space_bytes_string)
		free_space_bytes = free_space_bytes * 1024
	report_file.close()
	return free_space_bytes

	
###########################################################################
#To judge if the free space on the device is enough or not
#in: total size for all songs should be synchronized.
## TODO: add more generic algorithm here
###########################################################################
def check_if_enough_free_space(total_size):
#	available_space = get_free_space_on_device()
#	if available_space > total_size:
#		return True
#	else:
#		print >> sys.stderr, "No enough space on the phone, require is %d, available is %d." %(total_size, available_space)
#		return False
	return True
###########################################################################
#To run all commands within the command file.
#Please note: run each individual commands rather then the whole batch file
#   because of some strange issue
###########################################################################
def run_commands_in_file(command_file_name):
	try:
		command_file = open(command_file_name,"r")
	except IOError, message:
		print >> sys.stderr, "Command file could not be opened: ", message
		sys.exit(1)
	command_lines = command_file.readlines()
	total_lines = len(command_lines)
	current_line_num = 0
	for line in command_lines:
		if line.startswith('REM') == False:
			os.system(line)
			current_line_num = current_line_num + 1
			print "%d of %d copied" % (current_line_num,total_lines)

###########################################################################
# to prepare the media folder on the device
#create it directly, Android will handle it if it were there already
###########################################################################			
def prepare_media_folder():
	command_line = 'adb shell mkdir '+ android_media_folder_path + ' >nul'
	os.system(command_line)

###########################################################################
# to check the availability of the android device
#create it directly, Android will handle it if it were there already
#response when the device is there:
#    List of devices attached
#    HT92RLZ00432    device
#response when the device is not there
#    List of devices attached
###########################################################################			
def is_android_device_available():
	global temp_filename_to_be_deleted
	command_line = 'adb devices > ' + temp_filename_to_be_deleted
	os.system(command_line)
	try:
		report_file = open(temp_filename_to_be_deleted,"r")
	except IOError, message:
		print >> sys.stderr, "ADB devices result file could not be opened: ", message
		sys.exit(1)
	#something may wrong here because this file could be 3 lines if adb daemon has not been started yet
	report_lines = report_file.read()
#	if len(report_lines) == 3: #there is only one device, ok I can continue!
#	print 'result is ' , report_lines.count('device')
	if report_lines.count('device') == 2: #there is only one device, ok I can continue!
		report_file.close()
		return True
	report_file.close()
	return False	

###########################################################################
#To generate the list of all files on the device already
###########################################################################
def generate_file_list_already_on_device():
	device_file_report = temp_filename_to_be_deleted
	command_line = 'adb shell ls ' + android_media_folder_path + ' > ' + device_file_report
	os.system(command_line)
	try:
		report_file = open(device_file_report,"r")
	except IOError, message:
		print >> sys.stderr, "ADB ls Music result file could not be opened: ", message
		sys.exit(1)
	#something may wrong here because this file could be 3 lines if adb daemon has not been started yet
	device_file_list = report_file.read()
	return device_file_list


###########################################################################
#Main entry of the application
#To generate the command file and run it.
###########################################################################
def itunes_to_android(itunes_library_file_name, command_file_name):
	global g_playlist_set
	if is_android_device_available() == False:
		print >> sys.stderr, "There is no Android device, or more than one Android devoce. Please check!!!"
		sys.exit(1)
#	print 'itunes_library_file_name is ', itunes_library_file_name
	pl = iTunesXMLTrackParser(itunes_library_file_name)
	l = iTunesLibrary(pl.dictionary)
	# here we should go though all playlist in the list g_playlist_list
	
	playlist_parse_result = []
	for playlist in g_playlist_set:
		playlist_parse_result = playlist_parse_result + iTunesXMLPlaylistParser(itunes_library_file_name,playlist).playlist
#	print ' Print list in the main function'
#	print playlist_parse_result.playlist
	playlist_trackid_set = set(playlist_parse_result)
	try:
		output_file = open(command_file_name,"w")
	except IOError, message:
		print >> sys.stderr, "File could not be opened: ", message
		sys.exit(1)
	head_line = 'REM Generated automatically, DO NOT EDIT ME!!!'
	prepare_media_folder()
	file_list_already_on_device = generate_file_list_already_on_device()
#	head_line = 'Name, Size, Totoal time, Date added, Location, Comments'
	print >> output_file , head_line
	total_size = 0
	need_copy_file = False
	filename_to_be_copied_set = set()
	for song in l.songs:
#		content_line = song.name + ',' + str(song.size) + ',' + str(song.total_time) + ',' + str(song.date_added).replace(',','-') + ','+ song.location 
		#to check if the file should be 
		if check_if_song_to_be_synchronizaed(song,playlist_trackid_set) and is_new_song_for_device(song, file_list_already_on_device):
			#convert the location from apple-specific uri to the local path
			local_pathname = urllib.url2pathname(song.location.replace('file://localhost/','///'))
#			encoding = sys.getfilesystemencoding()
#			print encoding
#			print local_pathname.decode('utf-8').encode('gb2312')
#			print unicode(local_pathname, encoding)
#			uni_local_pathname = local_pathname.decode('utf-8').encode('cp936')
#			uni_local_pathname = unicode(local_pathname,'gb2312')
#			print uni_local_pathname
#			print >> output_file , 'adb push \"' + song.location.replace('file://localhost/','').replace('/','\\').replace('%20',' ') + '\"  /sdcard/Music'
			
			
			if local_pathname in filename_to_be_copied_set:
				print local_pathname, ' already there'
				print ''
			else:
				total_size = total_size + song.size
				filename_to_be_copied_set.add(local_pathname)
				need_copy_file = True
#		print content_line
#		+ ', ' + song.album_arist + ', ' + song.composer + ', '
#		+ song.album + ', '+ song.genre + ', '+ song.kind 
#		print song.size + ', '+ song.total_time + ', ' + song.track_number + ', ' + song.year + ', ' + song.date_modified + ', '+ song.date_added + ', '+ song.bit_rate + ', '+ song.sample_rate + ', '+ song.comments + ', '+ song.rating + ', '+ song.album_rating + ', '+ song.play_count + ', '+ song.location
	for filename in filename_to_be_copied_set:
		print >> output_file , 'adb push \"' + filename + '\"  /sdcard/AndroidMusic/ > nul'
	output_file.close()
	#print "total size to be copied is (%d)\n" % total_size
	if need_copy_file and check_if_enough_free_space(total_size):
	# to run the bat or run each individual commands?
		run_commands_in_file(command_file_name)	


###########################################################################
#to get the itunes library filename and path
#find from the command options first, otherwise hardcoded.
###########################################################################
#def get_itunes_lib_filename():
#	itunes_library_file=''
#	if len(sys.argv)==2:
#		itunes_library_file = sys.argv[1]
#	else:
#		print 'Will use the default iTunes library file'
#		itunes_library_file='''C:\Documents and Settings\lijie6\My Documents\My Music\iTunes\iTunes Music Library.xml'''
#	return itunes_library_file

###########################################################################
#to refresh the media list on the device 
#with this command: adb shell am broadcast -a android.intent.action.MEDIA_MOUNTED file:///sdcard
###########################################################################
def refresh_media_filelist_on_device():
	command_line = 'adb shell am broadcast -a android.intent.action.MEDIA_MOUNTED file:///sdcard > nul'
	os.system(command_line)
	command_line = 'adb shell am broadcast -a android.intent.action.MEDIA_MOUNTED file:///mnt/sdcard > nul'
	os.system(command_line)
###########################################################################
#to delete all temp files on the disk
#with this command: adb shell am broadcast -a android.intent.action.MEDIA_MOUNTED file:///sdcard
###########################################################################
def delete_temp_files():
	global command_list_file
	command_line = 'del /Q ' + temp_filename_to_be_deleted 
	os.system(command_line)
	command_line = 'del /Q ' + command_list_file 
	os.system(command_line)

def wipe_media_folder_on_device():
	command_line = 'adb shell rm -rf ' + android_media_folder_path + '* > nul'
	os.system(command_line)

def save_options_to_file(optlist):
	global option_file_name
	option_file = open(g_last_option_filename,"w")
	pickle.dump(optlist, option_file)
	option_file.close()

def load_options_from_file():
	option_list = []
	option_file = open(g_last_option_filename,"r")
	option_list = pickle.load(option_file)
	option_file.close()
	return option_list


optlist, my_args =getopt.getopt(sys.argv[1:],'',['playlist=','album=','artist='])
#print 'optlist= ', optlist
#print 'my_args= ', my_args
#check if it is the command for wipe
itunes_library_file_name=''
if 	len(my_args) == 0:
#	home_dir = os.getenv("HOME")
	#itunes_library_file_name = '''C:\Documents and Settings\lijie6\My Documents\My Music\iTunes\iTunes Music Library.xml'''
	itunes_library_file_name = os.path.join(os.getenv('USERPROFILE'), '''Music\iTunes\iTunes Music Library.xml''')
else:
	if my_args[0] == 'wipe':
		wipe_media_folder_on_device()
		refresh_media_filelist_on_device()
		exit('')
		
	if my_args[0] == 'last':
		optlist = load_options_from_file()

if len(optlist) == 0:
	print 'Command error! \n'
	print 'Command should be like this \n'
	print '''itunes2android.exe --playlist="Android,Windows Mobile,Symbian" --album="lijie_album1, lijie_album2" --artist="lijie_artist1,lijie_artist2" "C:\Documents and Settings\lijie6\My Documents\My Music\iTunes\iTunes Music Library.xml"'''
	print 'You should specify at least one from playlist/album/artist, you can ignore iTunes lib path if it is at the standard folder'
	exit('')
	
for o, a in optlist:
	if o == "--playlist":
		g_playlist_list = a.split(',')
	if o == "--album":
		g_album_list = a.split(',')
	if o == "--artist":
		g_artist_list = a.split(',')
# should strip all useless spaces in the list, and add to the set
for playlist in g_playlist_list:
	g_playlist_set.add(playlist.strip())
for album in g_album_list:
	g_album_set.add(album.strip())
for artist in g_artist_list:
	g_artist_set.add(artist.strip())
#	print 'o= ', o
#	print 'a= ', a

#itunes_library_file_name=get_itunes_lib_filename()
#print 'itunes_library_file_name= ', itunes_library_file_name
itunes_to_android(itunes_library_file_name, command_list_file)
refresh_media_filelist_on_device()
delete_temp_files()
save_options_to_file(optlist)