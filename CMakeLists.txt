# -*- coding: utf-8 -*-
#
#	Copyright 2010  Matthias Ableitner
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

### Python AI Interface
#
# Global variables set in this file:
# * BUILD_PYTHON_AIINTERFACE
# * PYTHON_AIINTERFACE_VERS
# * PYTHON_AIINTERFACE_TARGET
#


################################################################################
### BEGINN: MACROS_AND_FUNCTIONS
# Define macros and functions to be used in this file and by Skirmish AIs

# Native Skirmish AI configuration macro
# This will be called from native AIs at AI/Skirmish/*/CMakeLists.txt.
macro    (ConfigurePythonSkirmishAI)
	set(myDir                  "${CMAKE_CURRENT_SOURCE_DIR}")
	GetLastPathPart(dirName ${myDir})
	set(myName                 "${dirName}")
	set(mySourceDirRel         "${${mySourceDirRel_var}}") # Common values are "" or "src"
	set(additionalSources      ${${additionalSources_var}})
	set(additionalCompileFlags ${${additionalCompileFlags_var}})
	set(additionalLibraries    ${${additionalLibraries_var}})

	# Check if the user wants to compile the AI
	if    (BUILD_PYTHON_AIINTERFACE AND NOT myName MATCHES "${AI_EXCLUDE_REGEX}")
		set(BUILD_THIS_SKIRMISHAI TRUE)
	else  (BUILD_PYTHON_AIINTERFACE AND NOT myName MATCHES "${AI_EXCLUDE_REGEX}")
		set(BUILD_THIS_SKIRMISHAI FALSE)
		message("warning: ${myName} Skirmish AI will not be built!")
	endif (BUILD_PYTHON_AIINTERFACE AND NOT myName MATCHES "${AI_EXCLUDE_REGEX}")

	# Compile and install
	if    (BUILD_THIS_SKIRMISHAI)
		# Assemble meta data
		GetVersionFromFile(myVersion "${myDir}/VERSION")
		set(myTarget      "${myName}")
		set(myInstLibsDir "${SKIRMISH_AI_LIBS}/${myName}/${myVersion}")
		set(myInstDataDir "${SKIRMISH_AI_DATA}/${myName}/${myVersion}")
		MakeAbsolute(mySourceDir "${myDir}" "${mySourceDirRel}")

		SkirmishAIMessage(STATUS "Found Skirmish AI: ${myName} ${myVersion}")

		# Install the data files
		install(DIRECTORY "${myDir}/data/" DESTINATION ${myInstDataDir})
		install(DIRECTORY "${myDir}/src/" DESTINATION ${myInstDataDir} FILES_MATCHING PATTERN REGEX ".*\\.py$")
		# Install the library
	endif (BUILD_THIS_SKIRMISHAI)
endmacro (ConfigurePythonSkirmishAI)

### END: MACROS_AND_FUNCTIONS
################################################################################


set(myName            "Python")
set(myDir             "${CMAKE_CURRENT_SOURCE_DIR}")
set(mySourceDirRel    "src")


# Check if the user wants to compile the interface
if    ("${AI_TYPES}" STREQUAL "ALL" OR "${AI_TYPES}" STREQUAL "PYTHON")
	set(AI_TYPES_PYTHON TRUE)
else  ("${AI_TYPES}" STREQUAL "ALL" OR "${AI_TYPES}" STREQUAL "PYTHON")
	set(AI_TYPES_PYTHON FALSE)
endif ("${AI_TYPES}" STREQUAL "ALL" OR "${AI_TYPES}" STREQUAL "PYTHON")

FIND_PACKAGE(PythonInterp)
FIND_PACKAGE(PythonLibs)

# Check dependencies of the interface are met
if	(PYTHONINTERP_FOUND AND PYTHONLIBS_FOUND AND AI_TYPES_PYTHON)
	SetGlobal(BUILD_PYTHON_AIINTERFACE TRUE)
else    (PYTHONINTERP_FOUND AND PYTHONLIBS_FOUND AND AI_TYPES_PYTHON)
	SetGlobal(BUILD_PYTHON_AIINTERFACE FALSE)
	message ("warning: Python AI Interface will not be built!")
endif	(PYTHONINTERP_FOUND AND PYTHONLIBS_FOUND AND AI_TYPES_PYTHON)

# Build
if    (BUILD_PYTHON_AIINTERFACE)
	GetVersionFromFile(myVersion ${myDir}/VERSION)
	set(myTarget      "${myName}-AIInterface")

	INCLUDE_DIRECTORIES(${PYTHON_INCLUDE_PATH})
	set(myTarget      "${myName}-AIInterface")
	set(myLoader      "${myName}-Loader")
	set(myInstLibsDir ${AI_INTERFACES_LIBS}/${myName}/${myVersion})
	set(myInstDataDir ${AI_INTERFACES_DATA}/${myName}/${myVersion})
	set(myGeneratedDir "${CMAKE_CURRENT_BINARY_DIR}/src-generated")
	set(myBuilderDir "${CMAKE_CURRENT_BINARY_DIR}/src-generated-builder")
	MakeAbsolute(mySourceDir "${myDir}" "${mySourceDirRel}")

	AIInterfaceMessage(STATUS "Found AI Interface: ${myTarget} ${myVersion}")

	SetGlobal(PYTHON_AIINTERFACE_VERS   ${myVersion})
	SetGlobal(PYTHON_AIINTERFACE_TARGET ${myTarget})
#copy python files to generated dir, because python <=2.5 creates .pyc
	add_custom_command(
		COMMAND "cmake" ARGS "-E" "copy_directory" "builder" "${myBuilderDir}"
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		COMMENT "copying builder/ files to ${myBuilderDir}"
		DEPENDS "builder/template/*.py"
		OUTPUT
			"${myBuilderDir}/*.py"
			"${myBuilderDir}/template/*.py"
			"${myBuilderDir}/templates/*.c"
			"${myBuilderDir}/templates/*.py"
	)
#end copy
	add_custom_command(
		COMMAND ${PYTHON_EXECUTABLE}
		"${myBuilderDir}/generator.py"
		${PROJECT_SOURCE_DIR}
		"${myBuilderDir}/templates"
		${myGeneratedDir}
		WORKING_DIRECTORY ${myBuilderDir}
		COMMENT " Generating Python Interface" VERBATIM
		OUTPUT "${myGeneratedDir}/ai.c"
		OUTPUT "${myGeneratedDir}/PyAI/interface.py"
		DEPENDS
			"${myBuilderDir}/*.py"
			"${myBuilderDir}/template/*.py"
			"${myBuilderDir}/templates/*.c"
			"${myBuilderDir}/templates/*.py"
	)
	SET_DIRECTORY_PROPERTIES(PROPERTIES ADDITIONAL_MAKE_CLEAN_FILES "src/ai.c;src/PyAI/interface.py")
	set_source_files_properties("${myGeneratedDir}/ai.c" PROPERTIES GENERATED TRUE)
	aux_source_directory(${mySourceDir} mySources)
	INCLUDE_DIRECTORIES(${mySourceDir})
	add_library(${myTarget} MODULE ${mySources} ${ai_common_SRC} ${CUtils_SRC})
	add_library(${myLoader} MODULE ${ai_common_SRC} ${CUtils_SRC} "${myGeneratedDir}/ai.c")
	FixLibName(${myTarget})
	FixLibName(${myLoader})

	target_link_libraries(${myLoader} ${PYTHON_LIBRARY})
	set_target_properties(${myTarget} PROPERTIES OUTPUT_NAME "AIInterface")

	# Install the data files
	install(DIRECTORY "${myDir}/data/" DESTINATION "${myInstLibsDir}" FILES_MATCHING PATTERN REGEX "InterfaceInfo\\.lua$")
	install(DIRECTORY "${myDir}/data/" DESTINATION "${myInstDataDir}" FILES_MATCHING PATTERN REGEX "InterfaceInfo\\.lua$" EXCLUDE PATTERN "*")
	install(DIRECTORY "${myDir}/src/" DESTINATION "${myInstDataDir}" FILES_MATCHING PATTERN REGEX ".*\\.py$")
	install(DIRECTORY "${myGeneratedDir}/PyAI" DESTINATION "${myInstDataDir}" FILES_MATCHING PATTERN REGEX ".*\\.py$")
	# Install the library
	install(TARGETS   ${myTarget}      DESTINATION "${myInstLibsDir}")
	install(TARGETS   ${myLoader}      DESTINATION "${myInstLibsDir}")
endif (BUILD_PYTHON_AIINTERFACE)
