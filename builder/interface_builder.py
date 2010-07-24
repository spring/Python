# -*- coding: utf-8 -*-
#
#	Copyright 2010	Andreas Löscher
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

from helper import joinstrings

INDENTATION = "\t"
# indentation
fInd = INDENTATION
cInd = 2*INDENTATION

TEAMID = "teamModule._currentTeam.teamId"
CALLBACK = "teamModule._currentTeam.callback"

def buildclasses(funclist):

	retval = {}
	
	# special cases with no pattern
	special_cases = []
	
	for funcname in funclist:
		if not funcname:
			continue
		args = funclist[funcname][1]
		call="return "+CALLBACK+"."+funcname+"("
		# parse function name
		# standart pattern:
		#				Clb_<classname>*_[0<specialformat>0]<functionname>
		# special Cases:
		#				Clb_0MULTI1SIZE0Resource
		#				Clb_0MULTI1SIZE0UnitDef
		#				Clb_0MULTI1VALS0UnitDef
		#				seems like the following pattern:
		#				Clb_0MULTI1[SIZE/VALS]3<funcname>0<classname>
		#				and if no 3 between MULTI1SIZE and the next 0 then
		#				it is a count --> ResourceCount
		if funcname in special_cases:
			# no pattern here and hopefully not so many functions
			# manually translated
			pass
		elif funcname.startswith("Clb_0"):
			# special case
			# Same function of MULT1VALS and MULTI1SIZE as for ARRAY1SIZE and
			# ARRAY1VALS
			classes = [funcname.split("0")[-1]]
			# the challenge is to find good function names
			# Lets try the following:
			#			if MULTI1SIZE and MULT1VALS thing, then function name
			#			after second last argument name (because this is what you get)
			#			Clb_0MULTI1VALS0UnitDef(teamId, unitDefIds, unitDefIds_max)
			#			--> UnitDef.getIds()
			if "MULTI1SIZE" in funcname:
				# do not use this function directly
				# it is used within the same MULTI1VALS function
				# however, if this function does not exist, then its some kind of 
				# amount for the corresponding object
				i = funcname.find("MULTI1SIZE")
				valfunc = funcname[:i]+"MULTI1VALS"+funcname[i+len("MULTI1SIZE"):]
				if funclist.has_key(valfunc):
					continue
				else:
					pyfuncname="getCount"
					farg=""
					for name, type in args[1:]:
						farg += name+","
					pyarg = farg[:-1]
					farg = TEAMID+","+farg
					call = call+farg[:-1]+")"
			elif "MULTI1VALS" in funcname:
				pyfuncname = args[-2][0][:-2]
				classname = classes[-1]
				if classname.upper() in pyfuncname.upper():
					# allways starts with classname
					pyfuncname = pyfuncname[len(classname):]

				farg=""
				newargs = args[1:-2] # not the array and not the size
				
				
				for name, type in newargs:
					farg += name+","
				
				i = funcname.find("MULTI1VALS")
				sizefunc = funcname[:i]+"MULTI1SIZE"+funcname[i+len("MULTI1VALS"):]
				pyarg = farg[:-1]
				farg = TEAMID+","+farg
				farg += "None, "+CALLBACK+"."+sizefunc+"("+farg[:-1]+")"
				call = call+farg+")"
			elif "MULTI1FETCH3" in funcname:
				# Clb_0MULTI1FETCH3WeaponDefByName0WeaponDef
				pyfuncname = "get"+funcname.split("0")[1].split("3")[1]
				farg=""
				for name, type in args[1:]:
					farg += name+","
				pyarg = farg[:-1]
				farg = TEAMID+","+farg
				call = call+farg[:-1]+")"
			else:
				raise Exception("No pattern for function "+funcname)
			# END SPECIALCASE WITH PATTERN
		else:
			# standart case
			m=funcname.split("_")
			classes = m[1:-1]
			pyfuncname = m[-1]
			pyarg=""
			
			# check for special formats
			# ignore everything besides ARRAY1SIZE and ARRAY1VALS
			if "ARRAY1SIZE" in pyfuncname:
				# do not use this function directly
				# it is used within the same ARRAY1VALS function
				continue
			elif "ARRAY1VALS" in pyfuncname:
				farg=""
				newargs = args[1:-2] # not the array and not the size
				
				
				for name, type in newargs:
					farg += name+","
				
				i = funcname.find("ARRAY1VALS")
				sizefunc = funcname[:i]+"ARRAY1SIZE"+funcname[i+len("ARRAY1VALS"):]
				pyarg = farg[:-1]
				farg = TEAMID+","+farg
				farg += "None, "+CALLBACK+"."+sizefunc+"("+farg[:-1]+")"
				call = call+farg+")"
			elif "MAP" in pyfuncname:
				# in the current master branch, there are three MAP functions which in 
				# combination return some kind of dictionary:
				#		0MAP1SIZE0<funcname> -> size
				#		0MAP1KEYS0<funcname> -> keys
				#		0MAP1VALS0<funcname> -> values
				# only grep one function, because we do not need the rest
				if "VALS" in pyfuncname:
					# funcname == VALS function
					i = funcname.find("VALS")
					keyfunc = funcname[:i]+"KEYS"+funcname[i+len("VALS"):]

					farg=""
					newargs = args[1:-1] # not the array
					for name, type in newargs:
						farg += name+","
					tmp = "vals = "+CALLBACK+"."+funcname+"("+TEAMID+","+farg[:-1]+")\n"
					call = tmp + cInd+ "keys = "+CALLBACK+"."+keyfunc+"("+TEAMID+","+farg[:-1]+")\n"
					
					tmp = ""
					tmp += cInd + "return dict(dict_helper(vals, keys))\n"
					call = call + tmp
					# et voila, e have a dict
				else:
					continue
			else:
				farg=""
				for name, type in args[1:]:
					farg += name+","
				pyarg = farg[:-1]
				farg = TEAMID+","+farg
				call = call+farg[:-1]+")"

			# strip pyfuncname of specialformat
			pyfuncname = pyfuncname.split("0")[-1]
		docstring = "The arguments are:\n"
		assertstring = ""
		docu=False
		for arg in args[1:]:
			docu=True
			if "[]" in arg[0]  or "struct SAIFloat3*"==arg[1]:
				break
			docstring += "\t" + arg[0]+": "
			if "SAIFloat3" in arg[1]:
				docstring += "(float, float, float)"
				assertstring += cInd + "check_float3("+arg[0]+")\n"
			elif "char" in arg[1]:
				docstring += "string"
				assertstring += cInd + "assert isinstance("+arg[0]+", str)\n"
			elif "void" in arg[1]:
				docstring = "This function should not be used directly. Use the Command class instead. If you want to use this function directly, see the command class implementation for documentation."
				break
			elif "float" in arg[1]:
				docstring += arg[1]
				assertstring += cInd + "assert isinstance("+arg[0]+", float)\n"
			elif "int" in arg[1]:
				docstring += arg[1]
				assertstring += cInd + "assert isinstance("+arg[0]+", (int, long))\n"
				assertstring += cInd + arg[0] + "=int("+arg[0]+")\n"
			elif "bool" in arg[1]:
				docstring += arg[1]
				assertstring += cInd + "assert isinstance("+arg[0]+", int)\n"
			else:
				docstring += arg[1]
			docstring += "\n"
		if not docu:
			docstring= "no arguments"

		functionstring  = fInd + "@staticmethod\n"
		functionstring += fInd + "def "+pyfuncname+"("+pyarg+"):\n"
		functionstring += cInd + '"""'+ docstring + '"""\n'
		functionstring += assertstring
		functionstring += cInd + call + "\n"
		
		if not retval.has_key(classes[-1]):
			retval[classes[-1]] = []
		
		retval[classes[-1]].append(functionstring)
	return retval

def commandfuncs(commands):
	# generate functions for the command class
	funcs={}
	for command in commands:
		structname, members = commands[command]
		# extract functionname from structname
		# SSetMyHandicapCheatCommand
		# S<funcname>Commane
		funcname = structname[1].lower() + structname[2:-7]

		pyarglist = []
		dictbuild = "data = {"
		
		for member, mtype in members:
			if not "ret_" in member:
				pyarglist.append(member)
				dictbuild +="\""+member+"\":"+member+","
			else:
				# return data, give something stupid to the function
				if "int" in mtype:
					dictbuild += "\""+member+"\":0,"
				elif "SAIFloat3" in mtype:
					dictbuild += "\""+member+"\":(0,0,0),"
				elif "bool" in mtype:
					dictbuild += "\""+member+"\":0,"
				else:
					# do not convert function
					# if you really need those functions, you have to 
					# call them yourself
					continue
		if members:
			dictbuild = dictbuild[:-1]+"}"
		else:
			dictbuild += "}"
		
		code  = fInd+"@staticmethod\n"
		code += fInd+"def "+funcname+"("
		args = ""
		for arg in pyarglist:
			args += arg + ","
		if args:
			args = args[:-1]
		code += args+"):\n"
		code += cInd + dictbuild + "\n"
		code += cInd + "Command.id+=1" + "\n"
		code += cInd + "retval = "+CALLBACK+".Clb_Engine_handleCommand("+TEAMID+", -1, Command.id,"+command+",data)" + "\n"
		code += cInd + "if retval:\n"
		code += cInd + INDENTATION + "return Command.id, retval\n"
		code += cInd + "return Command.id\n"
		funcs[funcname]=code
	return funcs
