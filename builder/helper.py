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

def normstring(value):
	while (1):
		i = value.find("\n")
		if i>=0:
			value = value[:i]+value[(i+1):]
		else:
			break

		i = value.find("\t")
		if i>=0:
			value = value[:i]+value[(i+1):]
		else:
			break

	while (1):
		i = value.find("  ")
		if i>=0:
			value = value[:i]+value[(i+1):]
		else:
			break

	return value.strip()
	
def joinstrings(iterable, sep=" "):
	retval = ""
	for s in iterable:
		retval = retval +sep+ s
	return retval.strip()
	
def converter(ctype, cname):
	build = ""
	if "int" in ctype:
		build = "Py_BuildValue(\"i\", "+cname+")"
	elif "char" in ctype:
		build = "Py_BuildValue(\"s\", "+cname+")"
	elif "float" in ctype:
		build = "Py_BuildValue(\"f\", "+cname+")"
	elif "bool" in ctype:
		build = "Py_BuildValue(\"i\", (int)"+cname+")"
	elif "SAIFloat3" in ctype:
		build = "Py_BuildValue(\"o\", convert_SAIFloat3(&"+cname+"))"
	else:
		build = "Py_None"
	return build