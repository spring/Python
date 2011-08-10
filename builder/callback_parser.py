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
import regex, re

def buildcall(funcname, args, rettype):
	BEGIN_THREADS="PyGILState_STATE state = PyGILState_Ensure();\n"
	END_THREADS="PyGILState_Release(state);\n"
	reverse = False
	call = ""
	if rettype=="void":
		call += BEGIN_THREADS
		call +="callback->"
	else:
		call += rettype + " retval;\n"
		call += BEGIN_THREADS
		call += "retval = callback->"

	call += funcname+"("
	for index, (pname, ptype) in enumerate(args):
		call += "\n\t"
		varname = "arg"+str(index)
		if "[]" in pname or ptype=="struct SAIFloat3*":
			size = 1
			# need a list
			# listsize is in last parameter
			last_index=len(args)-1
			if ptype=="struct SAIFloat3*":
				prelude = ptype+" "
			else:
				prelude = ptype+"* "
			prelude+=varname+";\n"	
		
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

				# Find proper location to insert prelude into existing prelude
				i = call.find( BEGIN_THREADS )
				prelude = call[:i] + prelude
				prelude += "\tint size = "+sizefunccall+";\n"
				prelude += varname+"=malloc(sizeof("+ptype+")*size);\n\n"
				call = call[i:]
			call = prelude + call + varname + ","
			reverse = (ptype, varname, size)

		elif ptype=="int*":
			prelude = ptype + " " + varname + "="
			prelude += "build_intarray(PyTuple_GetItem(args, "+str(index)+"));\n"
			call += varname + ","
			call = prelude + call

		elif ptype=="int":
			prelude = ptype + " " + varname + "="
			prelude += "PyInt_AS_LONG(PyTuple_GetItem(args, "+str(index)+"));\n"
			call += varname + ","
			call = prelude + call

		elif ptype=="const char* const" or ptype=="const char*":
			prelude = ptype + " " + varname + "="
			prelude += "PyString_AS_STRING(PyTuple_GetItem(args, "+str(index)+"));\n"
			call += varname + ","
			call = prelude + call

		elif ptype=="bool":
			prelude = ptype + " " + varname + "="
			prelude += "(bool)PyInt_AS_LONG(PyTuple_GetItem(args,"+str(index)+"));\n"
			call += varname + ","
			call = prelude + call

		elif ptype=="struct SAIFloat3":
			prelude = ptype + " " + varname + "="
			prelude += "*(build_SAIFloat3(PyTuple_GetItem(args,"+str(index)+")));\n"
			call += varname + ","
			call = prelude + call

		elif ptype=="float":
			prelude = ptype + " " + varname + "="
			prelude += "PyFloat_AsDouble(PyTuple_GetItem(args, "+str(index)+"));\n"
			call += varname + ","
			call = prelude + call

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
	call += END_THREADS
	return call, reverse
		

def getcallback_functions(filename):
	f=open(filename, "r")

	stream = f.read()

	ouput = re.findall(regex.CALLBACK_FUNCTIONS, stream)

	output = re.findall(regex.CALLBACK_FUNCTIONS, stream)
	functionData = {}
	functionCalls = {}

	for retType, functionName, arguments in output:
		# build a list of tuples from the arguments string
		# [(name, type), (name, type), ...]
		argumentList = arguments.split(",")
		retType = retType.strip()
		for i, argument in enumerate(argumentList):
			argType, argName = argument.strip().rsplit(" ", 1)
			argumentList[i] = (argType, argName)

		call = buildcall(functionName, argumentList, retType)

		functionCalls[functionName] = call
		functionData[functionName]  = (functionName, argumentList, retType)

	return functionCalls, functionData

