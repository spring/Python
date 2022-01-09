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
macro    (configure_python_skirmish_ai)
	set(myDir                  "${CMAKE_CURRENT_SOURCE_DIR}")
	get_last_path_part(dirName ${myDir})
	set(myName                 "${dirName}")
	set(mySourceDirRel         "${${mySourceDirRel_var}}") # Common values are "" or "src"
	set(additionalSources      ${${additionalSources_var}})
	set(additionalCompileFlags ${${additionalCompileFlags_var}})
	set(additionalLibraries    ${${additionalLibraries_var}})

	# Check if the user wants to compile the AI
	if    (BUILD_PYTHON_AIINTERFACE AND NOT myName MATCHES "${AI_EXCLUDE_REGEX}")
		set(BUILD_THIS_SKIRMISHAI TRUE)
	else ()
		set(BUILD_THIS_SKIRMISHAI FALSE)
		message("warning: ${myName} Skirmish AI will not be built!")
	endif ()

	# Compile and install
	if    (BUILD_THIS_SKIRMISHAI)
		# Assemble meta data
		get_version_from_file(myVersion "${myDir}/VERSION")
		set(myTarget      "${myName}")
		set(myInstLibsDir "${SKIRMISH_AI_LIBS}/${myName}/${myVersion}")
		set(myInstDataDir "${SKIRMISH_AI_DATA}/${myName}/${myVersion}")
		make_absolute(mySourceDir "${myDir}" "${mySourceDirRel}")

		skirmish_ai_message(STATUS "Found Skirmish AI: ${myName} ${myVersion}")

		# Install the data files
		install(DIRECTORY "${myDir}/data/" DESTINATION ${myInstDataDir})
		install(DIRECTORY "${myDir}/src/" DESTINATION ${myInstDataDir} FILES_MATCHING PATTERN REGEX ".*\\.py$")
		# Install the library
	endif ()
endmacro ()

### END: MACROS_AND_FUNCTIONS
################################################################################


set(myName            "Python")
set(myDir             "${CMAKE_CURRENT_SOURCE_DIR}")
set(mySourceDirRel    "src")


# Check if the user wants to compile the interface
if    ("${AI_TYPES}" STREQUAL "ALL" OR "${AI_TYPES}" STREQUAL "PYTHON")
	set(AI_TYPES_PYTHON TRUE)
else ()
	set(AI_TYPES_PYTHON FALSE)
endif ()

if    (AI_TYPES_PYTHON AND myName MATCHES "${AI_EXCLUDE_REGEX}")
	set(AI_TYPES_PYTHON FALSE)
endif ()


find_package(PythonInterp)
find_package(PythonLibs)

# Check dependencies of the interface are met
if    (PYTHONINTERP_FOUND AND PYTHONLIBS_FOUND AND AI_TYPES_PYTHON)
	set_global(BUILD_PYTHON_AIINTERFACE TRUE)
else ()
	set_global(BUILD_PYTHON_AIINTERFACE FALSE)
	message ("warning: Python AI Interface will not be built!")
endif ()

# Build
if    (BUILD_PYTHON_AIINTERFACE)
	get_version_from_file(myVersion ${myDir}/VERSION)

	include_directories(${PYTHON_INCLUDE_PATH})
	set(myTarget      "${myName}-AIInterface")
	set(myNullPython  "NullPythonAI")
	set(myInstLibsDir ${AI_INTERFACES_LIBS}/${myName}/${myVersion})
	set(myInstDataDir ${AI_INTERFACES_DATA}/${myName}/${myVersion})
	set(myInstAIDir   ${SKIRMISH_AI_LIBS}/${myNullPython}/${myVersion})
	set(myGeneratedDir "${CMAKE_CURRENT_BINARY_DIR}/src-generated")
	set(myBuilderDir "${CMAKE_CURRENT_BINARY_DIR}/src-generated-builder")
	set(engineHeadersDir "${CMAKE_SOURCE_DIR}/rts/ExternalAI/Interface")

	make_absolute(mySourceDir "${myDir}" "${mySourceDirRel}")

	ai_interface_message(STATUS "Found AI Interface: ${myTarget} ${myVersion}")
	ai_interface_message(STATUS "Found Skirmish AI: ${myNullPython} ${myVersion}") # skirmish_ai_message() not defined here

	set_global(PYTHON_AIINTERFACE_VERS   ${myVersion})
	set_global(PYTHON_AIINTERFACE_TARGET ${myTarget})
	set(builderFiles
			"template/__init__.py"
			"template/context.py"
			"template/engine.py"
			"template/helper.py"
			"template/defaulttags.py"
			"interface_builder.py"
			"templates/interface.c"
			"templates/aiInterface.py"
			"templates/wrappai.c"
			"templates/converter.c"
			"templates/callback.c"
			"templates/command_wrapper.c"
			"templates/event_wrapper.c"
			"templates/create_command.c"
			"helper.py"
			"generator.py"
			"event_parser.py"
			"callback_parser.py")
	foreach (FILE ${builderFiles})
		list (APPEND myGeneratedFilesSourceDir "builder/${FILE}")
		list (APPEND myGeneratedFilesmyBuilderDir "${myBuilderDir}/${FILE}")
	endforeach ()
	set(myGenerateFiles
			${myGeneratedFilesmyBuilderDir}
			"${engineHeadersDir}/SSkirmishAICallback.h"
			"${engineHeadersDir}/AISEvents.h"
			"${engineHeadersDir}/AISCommands.h")

	# Copy python files to generated dir, because python <=2.5 creates .pyc
	add_custom_command(
		COMMAND "cmake" "-E" "copy_directory" "builder" "${myBuilderDir}"
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		COMMENT "copying builder/ files to ${myBuilderDir}"
		DEPENDS ${myGeneratedFilesSourceDir}
		OUTPUT ${myGeneratedFilesmyBuilderDir}
	)
	# Create the interface
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
		DEPENDS ${myGenerateFiles}
	)
	set_directory_properties(PROPERTIES ADDITIONAL_MAKE_CLEAN_FILES "src/ai.c;src/PyAI/interface.py")
	set_source_files_properties("${myGeneratedDir}/ai.c" PROPERTIES GENERATED TRUE)
	set_source_files_properties(${myGeneratedFilesmyBuilderDir} PROPERTIES GENERATED TRUE)

	aux_source_directory(${mySourceDir} mySources)
	include_directories(${mySourceDir})
	add_library(${myTarget} MODULE ${mySources} ${ai_common_SRC} ${CUtils_SRC} "${myGeneratedDir}/ai.c")
	fix_lib_name(${myTarget})

	set_target_properties(${myTarget} PROPERTIES OUTPUT_NAME "AIInterface")

	# Install the data files
	install(DIRECTORY "${myDir}/data/" DESTINATION "${myInstLibsDir}" FILES_MATCHING PATTERN REGEX "InterfaceInfo\\.lua$")
	install(DIRECTORY "${myDir}/data/" DESTINATION "${myInstDataDir}" FILES_MATCHING PATTERN REGEX "InterfaceInfo\\.lua$" EXCLUDE PATTERN "*")
	install(DIRECTORY "${myDir}/src/" DESTINATION "${myInstDataDir}" FILES_MATCHING PATTERN REGEX ".*\\.py$")
	install(DIRECTORY "${myGeneratedDir}/PyAI" DESTINATION "${myInstDataDir}" FILES_MATCHING PATTERN REGEX ".*\\.py$")
	# Install the library
	install(TARGETS   ${myTarget}      DESTINATION "${myInstLibsDir}")
	# Install the NullPythonAI
	install(DIRECTORY  "${myDir}/${myNullPython}/src/" DESTINATION "${myInstAIDir}" FILES_MATCHING PATTERN REGEX ".*\\.py$")
	install(DIRECTORY  "${myDir}/${myNullPython}/data/" DESTINATION "${myInstAIDir}" FILES_MATCHING PATTERN REGEX ".*\\.lua$")

endif ()
