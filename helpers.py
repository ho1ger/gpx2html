#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Holger Kinkelin
2015/01/02

A collection of small helper functions...
"""

# reads text from file
def readFile(file):
	try: 
		f = open(file, 'r')
		text = f.read()
		f.close()
		return text
	except:
		sys.exit("ERROR: unable to read file " + file)
		return ""


# writes text to file
def writeFile(file, text):
	try:
		f = open(file, 'w')
		f.write(text)
		f.close()
	except:
		sys.exit("ERROR: unable to write file " + file)
