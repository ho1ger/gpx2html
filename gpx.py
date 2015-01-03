#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Holger Kinkelin
2015/01/02
Script takes an gpx track, retrieves information from wikipedia about 
nearby interesting things, writes short teaser + link to full article to html file
Needs:
* geopy python module: https://pypi.python.org/pypi/geopy/1.7.0
* login for geonames, get a username here: http://www.geonames.org/login
"""

# some imports
from re import compile
from geopy.distance import vincenty
from geopy.geocoders import Nominatim
from urllib2 import urlopen
#import xml.dom.minidom as md
from xml.dom.minidom import parseString
import sys
import htmlEscaper, helpers

# some settings
delta = 5 #kilometer, not miles
user = "YOUR USER NAME" # 
lang = "de"

# some code \o/

# extracts the coordinates as tuples from the gpx file, returns an array
def parseGPX(input):
	#regexp for finding all the waypoints
	p = compile('lat="[0-9.-]+" lon="[0-9.-]+"')
	waypoints = p.findall(input)
	results = []
	if len(waypoints) > 0:
		# go through all found waypoints
		for waypoint in waypoints:
			# regexp for cleaning found waypoints
			p = compile('[0-9.-]+')
			waypointsClear = p.findall(waypoint)			
			if (len(waypointsClear) == 2):
				# adds the x/y coordinates as tuple to the results array
				results.append((waypointsClear[0], waypointsClear[1]))
			else:
				print "Error: cleaning waypoints."
	else:
		print "Error: Finding waypoints."
	return results


# currently not needed, however neat function
def reverse(waypoint):
	location = geolocator.reverse(waypoint[0] + ", " + waypoint[1])
	loc = location.raw["address"]
	try:
		return loc["road"], loc["postcode"], loc["town"], loc["state"], loc["country"]
	except:
		return "ERROR"


# returns true when some waypoint is further away as delta meters from some place
def deltaReached(pos, waypoint, delta):
	x = (pos[0], pos[1])
	y = (waypoint[0], waypoint[1])
	v = vincenty(x, y)
	v = str(v)
	v = v.replace(" km", "")
	v = float(v)
	if (v > delta):
		return True
	else:
		return False


# does some minidom black magic I do not fully understand
# copied from: https://docs.python.org/2/library/xml.dom.minidom.html
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


# retrievs info from wikipedia to one x / y coordinate
def retrieveInfo(pos, user, lang = "de"):
	x = pos[0]
	y = pos[1]
	url = "http://api.geonames.org/findNearbyWikipedia?lat={0}&lng={1}&username={2}&lang={3}".format(x, y, user, lang)
	response = urlopen(url)
	xml = response.read()
	# parse xml
	dom = parseString(xml)
	# go through the dom object, filter out interesting parts.
	# still ugly, needs to be rewritten
	results = []
	doParse = True
	i = 0
	while doParse:
		try:
			titledom = dom.getElementsByTagName("title")[i]
			title = getText(titledom.childNodes)
			summarydom = dom.getElementsByTagName("summary")[i]
			summary = getText(summarydom.childNodes)
			wikipediaUrldom = dom.getElementsByTagName("wikipediaUrl")[i]
			wikipediaUrl = getText(wikipediaUrldom.childNodes)
			results.append((title, summary, wikipediaUrl))
			i += 1
		except:
			doParse = False
	return results


# goes through all the waypoints, calls retrieveInfo when threshold to previous position > delta
def harvestInformation(waypoints):
	# the array with all information harvested
	results = []
	# startpoint is always included in our results
	pos = waypoints[0]
	print "Currently processing position: " + pos[0] + " / " + pos[1]
	results.extend(retrieveInfo(pos, user, lang))
	# process remaining waypoints...
	for waypoint in waypoints[1:]:
		# ... but do not call retrieveInfo for each waypoint, only if some distance is exceeded
		if deltaReached(pos, waypoint, delta):
			pos = waypoint
			print "Currently processing position: " + pos[0] + " / " + pos[1]
			#print reverse(pos) #not needed
			# get information for current waypoint
			results.extend(retrieveInfo(pos, user, lang))
	# also include the endpoint
	pos = waypoints[-1:][0] # [-1:] delivers an array with one element, hence we need [0]
	print "Currently processing position: " + pos[0] + " / " + pos[1]
	results.extend(retrieveInfo(pos, user, lang))

	return results


# removes all duplicates from harvested information
def filterToUniqueResults(results):
	# remove all duplicate entries. This list starts with the first entry of results
	filteredResults = [] 
	filteredResults.append(results[0])
	for i in range (1, len(results)):
		if results[i] not in filteredResults:
			filteredResults.append(results[i])
	return filteredResults


# converts filtered information to html code
def resultsToHTML(results):
	outputhtml = """
	<!DOCTYPE html>\n
	<html>\n
	<body>\n
	"""
	for fr in filteredResults:
		fr0 = fr[0].encode('utf8')
		fr0 = htmlEscaper.htmlEscape(fr0)
		fr1 = fr[1].encode('utf8')
		fr1 = htmlEscaper.htmlEscape(fr1)
		fr2 = fr[2].encode('utf8')
		fr2 = htmlEscaper.htmlEscape(fr2)
		outputhtml += "<h1>" + fr0 + "</h1>\n"
		outputhtml += "<p>" + fr1 + "</p>\n"
		outputhtml += "<p><a href='" + fr2 + "'>Link: " + fr0 + "</a></p>\n"
	outputhtml += """
	</body>\n
	</html>\n
	"""
	return outputhtml

# ------------------------------------------------------------

# open the gpx file
track = sys.argv[1]
input = helpers.readFile(track)

# get the waypoints as array of (x, y) tuples
waypoints = parseGPX(input)

# not needed
#geolocator = Nominatim() 

# get info to all waypoints
results = harvestInformation(waypoints)

# remove the duplicates
filteredResults = filterToUniqueResults(results)

# convert to html
outputhtml = resultsToHTML(filteredResults)

# write html to file named like the input gpx file + .html
helpers.writeFile(track+".html", outputhtml)

