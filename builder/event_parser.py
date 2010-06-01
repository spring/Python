# -*- coding: utf-8 -*-
#
#	Copyright 2010  Andreas Löscher
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#	@author Andreas Löscher
#	@author Matthias Ableitner <spam@abma.de>
#

from helper import normstring, joinstrings

def parse_enums(filename):
	""" String without comments and defines
	"""
	f=open(filename, "r")
	
	line = ""             # line to be processed
	skipnext=False        # are we in an unfinished multiline comment?
	retval=[]             # return value
	
	events = {}
	inenum = False
	inenum = False
	indefine = False
	
	structname =""
	
	structs = {}          # Eventname -> (Structname, {membername->membertype})
	
	pairs = {}
	
	for actline in f.readlines():
		# ignore exter "c"{
		if 'extern "C"' in actline:
			continue
		
		# ignore lines starting with defines
		if ("#" in actline):
			if "\\" in actline:
				indefine = True
			continue
		if indefine:
			if "\\" in actline:
				continue
			else:
				indefine = False
				continue
		
		# skip /* */ comments
		cont=False # continue after while loop?
		while (1): # for cases where "/* com */ /* com */"in one line
			if not skipnext and "/*" in actline:
				skipnext=True
				cont=True
				break
			if skipnext and "*/" in actline:
				skipnext=False
				i = actline.find("*/")
				actline=actline[(i+2):]
			if skipnext:
				cont=True
				break
			break
		if cont:
			cont=False
			continue
		
		# remove // comments
		if ("//" in actline) and not ("};" in actline):
			i = actline.find("//")
			actline = actline[:i]
		if (not inenum) and ("enum" in actline):
			# store structname
			inenum=True
			continue
		if inenum:
			if "};" in actline:
				vallist = normstring(line).split(",")
				for val in vallist:
					tmp =  val.split("=")
					if len(tmp)>1:
						pairs[tmp[0].strip()] = int(tmp[-1])
				break
			else:
				line = line + actline
	f.close()
	return pairs


def parse_structs(filename):
	""" String without comments and defines
	"""
	f=open(filename, "r")
	
	line = ""             # line to be processed
	skipnext=False        # are we in an unfinished multiline comment?
	retval=[]             # return value
	
	events = {}
	inenum = False
	instruct = False
	indefine = False
	
	structname =""
	
	structs = {}          # Eventname -> (Structname, {membername->membertype})
	
	for actline in f.readlines():
		# ignore exter "c"{
		if 'extern "C"' in actline:
			continue
		
		# ignore lines starting with defines
		if ("#" in actline):
			if "\\" in actline:
				indefine = True
			continue
		if indefine:
			if "\\" in actline:
				continue
			else:
				indefine = False
				continue
		
		# skip /* */ comments
		cont=False # continue after while loop?
		while (1): # for cases where "/* com */ /* com */"in one line
			if not skipnext and "/*" in actline:
				skipnext=True
				cont=True
				break
			if skipnext and "*/" in actline:
				skipnext=False
				i = actline.find("*/")
				actline=actline[(i+2):]
			if skipnext:
				cont=True
				break
			break
		if cont:
			cont=False
			continue
		
		# remove // comments
		if ("//" in actline) and not ("};" in actline):
			i = actline.find("//")
			actline = actline[:i]
		
		if (not instruct) and ("struct" in actline):
			# store structname
			structname = normstring(actline).split(" ")[1]
			instruct=True
			continue
		if instruct:
			if "};" in actline:
				event = (normstring(actline).split(" "))[-1]
				
				# process struct
				memberline = normstring(line).split(";")
				memberline.pop()
				
				members = []
				
				for member in memberline:
					member=normstring(member).split(" ")
					members.append((member[-1], joinstrings(member[:-1])))

				structs[event] = (structname, members)
				
				line = ""
				instruct=False
				continue
			else:
				line = line + actline
	f.close()
	return structs

def getevents(filename):
	# Eventname -> (Structname, {membername->membertype})
	events = parse_structs(filename)
 
	for event in events:
		sname, members = events[event]
		argstring = ""
		formatstring = "{"
		for member, mtype in members:
			if "int*" in mtype:
				# special case, it is EVENT_PLAYER_COMMAND
				# make this as generic as possible
				nummember = "num"+member[0].upper()+member[1:]
				formatstring+="sO"
				argstring+="\""+member+"\","
				argstring+="convert_intarray(((struct "+sname+"*)data)->"+member+", ((struct "+sname+"*)data)->"+nummember+"),"
			elif "int" in mtype:
				formatstring+="si"
				argstring+="\""+member+"\","
				argstring+="((struct "+sname+"*)data)->"+member+","
			elif "char" in mtype:
				formatstring+="ss"
				argstring+="\""+member+"\","
				argstring+="((struct "+sname+"*)data)->"+member+","
			elif "float" in mtype:
				formatstring+="sf"
				argstring+="\""+member+"\","
				argstring+="((struct "+sname+"*)data)->"+member+","
			elif "bool" in mtype:
				formatstring+="si"
				argstring+="\""+member+"\","
				argstring+="((struct "+sname+"*)data)->"+member+","
			elif "SAIFloat3" in mtype:
				formatstring+="sO"
				argstring+="\""+member+"\","
				argstring+="convert_SAIFloat3(&(((struct "+sname+"*)data)->"+member+")),"
			elif "SSkirmishAICallback" in mtype:
				formatstring+="sO"
				argstring+="\""+member+"\","
				argstring+="PyAICallback_New(((struct "+sname+"*)data)->"+member+"),"

		formatstring = formatstring+ "}"
		argstring = argstring[:-1]
		
		buildstring = "Py_BuildValue(\""+formatstring+"\","+argstring+")"
		events[event] = buildstring
	return events


def getcommands(filename):
	# Commandname -> (Structname, {membername->membertype})
	commands = parse_structs(filename)
	return commands
