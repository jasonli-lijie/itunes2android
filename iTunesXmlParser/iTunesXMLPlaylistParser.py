import re
class iTunesXMLPlaylistParser:
	def __init__(self,xmlLibrary,playlistTag):
		f = open(xmlLibrary)
		s = f.read()
		lines = s.split("\n")
		self.my_playlist_tag = playlistTag
		self.playlist = self.parser(lines)

	#Sample: <integer>644</integer> to 644
	#Pay attention to the encoding		
	def getValue(self,restOfLine):
		value = re.sub("<.*?>","",restOfLine)
		u = unicode(value,"utf-8")
		cleanValue = u.encode("ascii","xmlcharrefreplace")
		return cleanValue

	#Sample: line='''<key>Name</key><string>Google Custom Search</string>'''
	#key='''Name'''
	#restOfLine='''<string>Google Custom Search</string>'''
	def keyAndRestOfLine(self,line):
		rawkey = re.search('<key>(.*?)</key>',line).group(0)
		key = re.sub("</*key>","",rawkey)
		restOfLine = re.sub("<key>.*?</key>","",line).strip()
		return key,restOfLine

	def parser(self,lines):
		dict_level = 0
		array_level = 0
		playlist = []
		in_playlist = False
		in_my_playlist = False
		for line in lines:
			if re.search('<dict>',line):
				dict_level += 1
			if re.search('</dict>',line):
				dict_level -= 1
			if re.search('<key>Playlists</key>', line):
				in_playlist = True
				array_level = 0
				continue  #go to next loop directly
		#although playlist is always at the end of the xml file, I should still handle the end of it
		#to find the end of the <array> tag
			if in_playlist == True:
				if re.search('<array>', line):
					array_level += 1
					continue
				if re.search('</array>', line):
					array_level -= 1
					if array_level == 0:
						in_playlist = False
						return playlist
				if dict_level == 2 and array_level == 1:
					search_string = '''<key>Name</key><string>'''+self.my_playlist_tag.strip()+'''</string>'''
#					print 'find ', search_string, ' in ', line
					if re.search(search_string.strip(), line):
#						print 'found the android playlist in line ', line
						in_my_playlist = True
						continue
				if in_my_playlist:
#					print 'to parse line within my playlist: ', line
#					print "dict_level = %d, array_level = %d" % (dict_level , array_level)
					if dict_level < 2:
#						print 'in_my_playlist == True and dict_level < 2: now exit'
						in_my_playlist = False
#						print playlist
						return playlist
					if array_level == 2 and dict_level == 3 and re.search('<key>(.*?)</key>',line):
#						print 'got a line', line
						key,restOfLine = self.keyAndRestOfLine(line)
						track_id = self.getValue(restOfLine)
#						print 'Will apend ' , track_id, ' to the list'
						playlist.append(track_id)
		return playlist
