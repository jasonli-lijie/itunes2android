import re
class iTunesXMLTrackParser:
	def __init__(self,xmlLibrary):
		f = open(xmlLibrary)
		s = f.read()
		lines = s.split("\n")
		self.dictionary = self.parser(lines)

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

#get all tracks in the iTunes library
	def parser(self,lines):
		dict_level = 0
		songs = {}
		inSong = False
		for line in lines:
			if re.search('<dict>',line):
				dict_level += 1
			if re.search('</dict>',line):
				dict_level -= 1
				inSong = False
				songs[songkey] = temp
			if dict_level == 2 and re.search('<key>(.*?)</key>',line):
				rawkey = re.search('<key>(.*?)</key>',line).group(0)
				songkey = re.sub("</*key>","",rawkey)
				inSong = True
				temp = {}
			if dict_level == 3  and re.search('<key>(.*?)</key>',line):
#go though <key>Tracks</key> only, will not care about playlist
				key,restOfLine = self.keyAndRestOfLine(line)
				temp[key] = self.getValue(restOfLine)
			if len(songs) > 0 and dict_level < 2:
				return songs
		return songs
