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

def buildcall(funcname, args, rettype):
	reverse = False
	call = ""
	if rettype=="void":
		call +="callback->"
	else:
		call += rettype + " retval;\n"
		call += "retval = callback->"
	call += funcname+"("
	for index, (pname, ptype) in enumerate(args):
		call += "\n\t"
		if "[]" in pname or ptype=="struct SAIFloat3*":
			size = 1
			# need a list
			# listsize is in last parameter
			last_index=len(args)-1
			varname = "extra"+str(index)
			if ptype=="struct SAIFloat3*":
				prelude = ptype+" "+varname+";\n"
			else:
				prelude = ptype+"* "+varname+";\n"
			
			if not "MAP" in funcname:
				# get the listsize from the prelast parameter
				if ptype=="struct SAIFloat3*":
					prelude += varname+"=malloc(sizeof("+ptype[:-1]+")*PyInt_AS_LONG(PyTuple_GetItem(args, "+str(last_index)+")));\n"
				else:
					prelude += varname+"=malloc(sizeof("+ptype+")*PyInt_AS_LONG(PyTuple_GetItem(args, "+str(last_index)+")));\n"
			else:
				# MAP functions use another function for the list size and you cannot specify the max listlength
				# as parameter
				i = funcname.find("KEYS")
				if i==-1:
					i = funcname.find("VALS")
				sizefuncname = funcname[:i]+"SIZE"+funcname[i+4:]
				sizefunccall = "callback->"+sizefuncname+"("
				# now the parameters, if we are at the list, take all other parameters befor"
				i = call.rfind(funcname) + len(funcname) + 1
				params = call[i:]
				i = params.rfind(",")
				params = params[:i]+params[i+1:]
				sizefunccall += params
				sizefunccall += "\t)"
				size="size"
				prelude += "\tint size = "+sizefunccall+";\n\t"+varname+"=malloc(sizeof("+ptype+")*size);\n\t"
			call = prelude + call + varname + ","
			reverse = (ptype, varname, size)
		elif ptype=="int*":
			call += "build_intarray(PyTuple_GetItem(args, "+str(index)+")),"
		elif ptype=="int":
			call += "PyInt_AS_LONG(PyTuple_GetItem(args, "+str(index)+")),"
		elif ptype=="const char* const" or ptype=="const char*":
			call += "PyString_AS_STRING(PyTuple_GetItem(args, "+str(index)+")),"
		elif ptype=="bool":
			call += "(bool)PyInt_AS_LONG(PyTuple_GetItem(args,"+str(index)+")),"
		elif ptype=="struct SAIFloat3":
			call += "*(build_SAIFloat3(PyTuple_GetItem(args,"+str(index)+"))),"
		elif ptype=="float":
			call += "PyFloat_AsDouble(PyTuple_GetItem(args, "+str(index)+")),"
		elif ("void*") in ptype and ("commandData" in pname):
			prelude = "void* commandData="
			prelude += "command_convert((int)PyInt_AS_LONG(PyTuple_GetItem(args, "+str(index-1)+")), PyTuple_GetItem(args, "+str(index)+"));\n"
			call += "commandData,"
			call = prelude + call
			reverse = ("void","command_reverse((int)PyInt_AS_LONG(PyTuple_GetItem(args, "+str(index-1)+")),commandData)",1)
		else:
			call += "NULL,"

	first ="const struct SSkirmishAICallback* callback = ((PyAICallbackObject*)ob)->callback;\n"
	call=first + call[:-1]+");\n"
	return call, reverse
		

def getcallback_functions(filename):
	f=open(filename, "r")

	line = ""         # line to be processed
	skipnext=False    # are we in an unfinished multiline comment?
	retval= {}        # return value
	plainlist = {}

	for actline in f.readlines():
		# ignore exter "c"{
		if 'extern "C"' in actline:
			continue

		# ignore lines starting with defines
		if ("#" in actline):
			continue
		
		# skip /* */ comments
		cont=False # continue after while loop?
		while (1): # for cases where "/* com */ /* com */"in one line
			if not skipnext and "/*" in actline:
				skipnext=True
				cont=True
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
		if "//" in actline:
			i = actline.find("//")
			actline = actline[:i]

		# ignore struct define line
		if ("struct" in actline) and ("SSkirmishAICallback" in actline):
			continue

		# join lines to one statement (in this case function definition in struct)
		if actline.find(";")>0:
			line+=actline
		else:
			line = line[:-1] if line.endswith("\n") else line
			line = line+actline
			continue
		
		# split lines on CALLING_CONV
		# first thing before CALLING_CONV is return type
		i=line.find("(CALLING_CONV")
		rettype = line[:i].strip()
		
		# first thing after CALLING_CONV is function name
		remains = line[(i+len("(CALLING_CONV")):]
		i=remains.find("(")
		funcname = remains[:i].strip()[1:-1]
		
		# the stuff in the brakets after the function name are the
		# arguments with types
		remains = remains[i+1:]
		remains = normstring(remains[:remains.find(")")])
		args = remains.split(",")
		arglist = []

		for arg in args:
			aa=arg.strip().split(" ")
			key = aa[-1]
			value = joinstrings(aa[:-1])
			#if "[]" in key:
				#key=key.replace("[]", " ")
				#value+="*"
			arglist.append((key, value))
		
		plainlist[funcname]=(retval, arglist)
		
		call, reverse = buildcall(funcname, arglist, rettype)
		
		if not reverse:
			retbuild = ""
			if "int" in rettype:
				retbuild = "Py_BuildValue(\"i\", retval)"
			elif "char" in rettype:
				retbuild = "Py_BuildValue(\"s\", retval)"
			elif "float" in rettype:
				retbuild = "Py_BuildValue(\"f\", retval)"
			elif "bool" in rettype:
				retbuild = "Py_BuildValue(\"i\", (int)retval)"
			elif "SAIFloat3" in rettype:
				retbuild = "Py_BuildValue(\"O\", convert_SAIFloat3(&retval))"
			else:
				retbuild = "Py_None"
			call +="return "+retbuild+";"
		else:
			ptype, pname, size = reverse
			if "command_reverse" in pname:
				# special case: command struct my return a value
				call += "PyObject *pyreturn="+pname+";\n"
				call += "FREE(commandData);\n"
				call += "return pyreturn;"
			else:
				# an array was filled and the amount of data is given in the return value
				# in this case do not give back the size of the array but convert everything into
				# alist and return the list
				if not "MAP" in funcname:
					listsize = "retval"
				else:
					listsize = str(size)
					
				if ptype=="float":
					builditem="PyFloat_FromDouble("
				elif ptype=="int" or ptype=="unsigned short" or ptype=="unsigned char":
					builditem="PyInt_FromLong("
				elif ptype=="const char*":
					builditem="PyString_FromString("
				elif ptype=="struct SAIFloat3*":
					builditem="convert_SAIFloat3(&"
				else:
					raw_input("error: "+ptype+call)

				prelude = "PyObject* list;\nint i;\n"
				postlude = "list = PyList_New("+listsize+");\n"
				postlude += "for (i=0;i<"+listsize+";i++) PyList_SetItem(list, i, "+builditem+pname+"[i]));\n"
				postlude += "FREE("+pname+");\n"
				postlude += "return list;"
				call = prelude + call + postlude

		if funcname:
			retval[funcname]=call
		
		# reset line
		line=""
	return retval, plainlist

