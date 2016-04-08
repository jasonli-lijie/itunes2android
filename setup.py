from distutils.core import setup
import py2exe

setup(console=['itunes2android.py', 'iTunesXmlParser\__init__.py','iTunesXmlParser\iTunesLibrary.py','iTunesXmlParser\iTunesSong.py', 'iTunesXmlParser\iTunesXMLPlaylistParser.py','iTunesXmlParser\iTunesXMLTrackParser.py'])

 
