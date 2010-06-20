/*
	Copyright (c) 2010 Matthias Ableitner <spam@abma.de>

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.

	@author Matthias Ableitner <spam@abma.de>
	@author Andreas Löscher
*/

#include <Python.h>

#include "ai.h"
#include "InterfaceExport.h"


#include "InterfaceDefines.h"
#include "CUtils/Util.h"
#include "CUtils/SimpleLog.h"
#include "CUtils/SharedLibrary.h"

#include "ExternalAI/Interface/SAIInterfaceLibrary.h"
#include "ExternalAI/Interface/SAIInterfaceCallback.h"
#include "ExternalAI/Interface/ELevelOfSupport.h"
#include "ExternalAI/Interface/SSkirmishAILibrary.h"

#define INTERFACE_PROPERTIES_FILE "interface.properties"

static int interfaceId = -1;
static const struct SAIInterfaceCallback* callback = NULL;

sharedLib_t hPython;
#ifdef WIN32
#define PATH_SEPERATOR "\\"
#else
#define PATH_SEPERATOR "/"
#endif
int loadPythonInterpreter(const char* logFileName, bool useTimeStamps, int logLevel){
	const char* pythonNames [] = { 
		"python3.1", "python31",
		"python2.6", "python26",
		"python2.5", "python25",
		"python2.4", "python24",
		NULL };

	char filename[FILEPATH_MAXSIZE];
	char logBuf[FILEPATH_MAXSIZE];
	int i=0;
	while((pythonNames[i]!=NULL)&&(hPython==NULL)){
		//create platform independant libname (.dll, .so, ...)
		sharedLib_createFullLibName(pythonNames[i],(char *)&filename,FILEPATH_MAXSIZE);
		simpleLog_log("Trying to load %s",filename);
		hPython=sharedLib_load(filename);
		i++;
	}
	if (hPython == NULL){
		snprintf(logBuf,FILEPATH_MAXSIZE,"Error loading python_loader: %s, is python installed?",filename);
		callback->Log_exception(interfaceId,(char*)&logBuf,0,true);
		return 1;
	}
	bindPythonFunctions(hPython);
	simpleLog_log("Python loaded successfully");
	python_load(callback,interfaceId);
	return 0;
}

/**
* This function is called right after the library is dynamically loaded.
* It can be used to initialize variables and to check or prepare
* the environment (os, engine, filesystem, ...).
* @see releaseStatic()
*
* [optional]
* An AI Interface not exporting this function is still valid.
*
* opens the log file and tries to load an python interpreter and initalizes
* the basic stuff, the ai is then loaded in 
*
*
*
* @param       staticGlobalData contains global data about the engine and the
*                           environment; is guaranteed to be valid till
*                           releaseStatic() is called.
* @return     0: ok
*          != 0: error
*/
EXPORT(int)
initStatic(int _interfaceId, const struct SAIInterfaceCallback* _callback)
{
	// initialize C part of the interface
	interfaceId = _interfaceId;
	callback = _callback;
	
	const char* myShortName = callback->AIInterface_Info_getValueByKey(interfaceId,
		AI_INTERFACE_PROPERTY_SHORT_NAME);
	const char* const myVersion = callback->AIInterface_Info_getValueByKey(interfaceId,
		AI_INTERFACE_PROPERTY_VERSION);

	static const int maxProps = 64;
	const char* propKeys[maxProps];
	char* propValues[maxProps];
	int numProps = 0;

	// ### read the interface config file (optional) ###
	char propFilePath[FILEPATH_MAXSIZE];

	// eg: "~/.spring/AI/Interfaces/Python/${INTERFACE_PROPERTIES_FILE}"
	bool propFileFetched = callback->DataDirs_locatePath(interfaceId,
		propFilePath, FILEPATH_MAXSIZE,
		INTERFACE_PROPERTIES_FILE, false, false, false, false);
	if (!propFileFetched) {
		// if the version specific file does not exist,
		// try to get the common one
		propFileFetched = callback->DataDirs_locatePath(interfaceId,
			propFilePath, FILEPATH_MAXSIZE,
			INTERFACE_PROPERTIES_FILE, false, false, false, true);
	}
	if (propFileFetched) {
		numProps = util_parsePropertiesFile(propFilePath,
			propKeys, (const char**)propValues, maxProps);

		static const unsigned int ddw_sizeMax = 1024;
		char ddw[ddw_sizeMax];
		// eg: "~/.spring/AI/Interfaces/Python/${INTERFACE_PROPERTIES_FILE}"
		bool ddwFetched = callback->DataDirs_locatePath(interfaceId,
			ddw, ddw_sizeMax,
			"", true, true, true, false);
		if (!ddwFetched) {
			simpleLog_logL(SIMPLELOG_LEVEL_ERROR,
				"Failed locating writeable data-dir \"%s\"", ddw);
		}
		int p;
		for (p=0; p < numProps; ++p) {
			char* propValue_tmp = util_allocStrReplaceStr(propValues[p],
				"${home-dir}", ddw);
// 			char* propValue_tmp = util_allocStrReplaceStr(propValues[p],
// 				"${home-dir}/", "");
			free(propValues[p]);
			propValues[p] = propValue_tmp;
		}
	}

	// ### try to fetch the log-level from the properties ###
	int logLevel = SIMPLELOG_LEVEL_FINEST;
	const char* logLevel_str =
		util_map_getValueByKey(numProps, propKeys, (const char**)propValues,
		"log.level");
	if (logLevel_str != NULL) {
		int logLevel_tmp = atoi(logLevel_str);
		if (logLevel_tmp >= SIMPLELOG_LEVEL_ERROR
			&& logLevel_tmp <= SIMPLELOG_LEVEL_FINEST) {
			logLevel = logLevel_tmp;
		}
	}

	// ### try to fetch whether to use time-stamps from the properties ###
	bool useTimeStamps = true;
	const char* useTimeStamps_str =
		util_map_getValueByKey(numProps, propKeys, (const char**)propValues,
		"log.useTimeStamps");
	if (useTimeStamps_str != NULL) {
		useTimeStamps = util_strToBool(useTimeStamps_str);
	}

	// ### init the log file ###
	char* logFile = util_allocStrCpy(
		util_map_getValueByKey(numProps, propKeys, (const char**)propValues,
		"log.file"));
	if (logFile == NULL) {
		logFile = util_allocStrCatFSPath(2, "log", MY_LOG_FILE);
	}

	static const unsigned int logFilePath_sizeMax = 1024;
	char logFilePath[logFilePath_sizeMax];
	// eg: "~/.spring/AI/Interfaces/Python/${INTERFACE_PROPERTIES_FILE}"
	bool logFileFetched = callback->DataDirs_locatePath(interfaceId,
		logFilePath, logFilePath_sizeMax,
		logFile, true, true, false, false);

	if (logFileFetched) {
		simpleLog_init(logFilePath, useTimeStamps, logLevel, false);
	} else {
		simpleLog_logL(SIMPLELOG_LEVEL_ERROR,
				"Failed initializing log-file \"%s\"", logFileFetched);
	}

	// log settings loaded from interface config file
	if (propFileFetched) {
		simpleLog_logL(SIMPLELOG_LEVEL_FINE, "settings loaded from: %s",
			propFilePath);
		int p;
		for (p=0; p < numProps; ++p) {
			simpleLog_logL(SIMPLELOG_LEVEL_FINE, "\t%i: %s = %s",
				p, propKeys[p], propValues[p]);
		}
	} else {
		simpleLog_logL(SIMPLELOG_LEVEL_FINE, "settings NOT loaded from: %s",
			propFilePath);
	}

	simpleLog_log("This is the log-file of the %s v%s AI Interface",
		myShortName, myVersion);
	simpleLog_log("Using read/write data-directory: %s",
		callback->DataDirs_getWriteableDir(interfaceId));
	simpleLog_log("Using log file: %s", logFilePath);
	simpleLog_log("Loading Python");
	int res=loadPythonInterpreter(logFilePath, useTimeStamps, logLevel);
	FREE(logFile);
	return res;
}
/**
* This function is called right right before the library is unloaded.
* It can be used to deinitialize variables and to cleanup the environment,
* for example the filesystem.
*
* See also initStatic().
*
* [optional]
* An AI Interface not exporting this function is still valid.
*
* @return     0: ok
*          != 0: error
*/
EXPORT(int)
releaseStatic()
{
	simpleLog_log("releaseStatic()");
	python_unload();
	hPython=NULL;
	// release C part of the interface
	util_finalize();
	return 0;
}


/**
* Level of Support for a specific engine version and AI interface version.
*
* [optional]
* An AI not exporting this function is still valid.
*
* @return      the level of support for the supplied engine and AI interface
*                      versions
*/
EXPORT(enum LevelOfSupport)
getLevelOfSupportFor(const char* engineVersion, int engineAIInterfaceGeneratedVersion)
{
	simpleLog_log("getLevelOfSupportFor()");
	return LOS_Unknown;
}

// skirmish AI methods
static struct SSkirmishAILibrary* mySSkirmishAILibrary = NULL;

enum LevelOfSupport CALLING_CONV proxy_skirmishAI_getLevelOfSupportFor(
		int teamId,
		const char* engineVersionString, int engineVersionNumber,
		const char* aiInterfaceShortName, const char* aiInterfaceVersion) {

	return LOS_Unknown;
}

EXPORT(const struct SSkirmishAILibrary*)
loadSkirmishAILibrary(const char* const shortName, const char* const version) 
{
	simpleLog_logL(SIMPLELOG_LEVEL_FINE, "loadSkirmishAILibrary()");
	if (mySSkirmishAILibrary == NULL) {
		mySSkirmishAILibrary =
			(struct SSkirmishAILibrary*) malloc(sizeof(struct SSkirmishAILibrary));

		mySSkirmishAILibrary->getLevelOfSupportFor =
			&proxy_skirmishAI_getLevelOfSupportFor;

		mySSkirmishAILibrary->init = &python_init;
		mySSkirmishAILibrary->release = &python_release;
		mySSkirmishAILibrary->handleEvent = &python_handleEvent;
	}
	simpleLog_logL(SIMPLELOG_LEVEL_FINE, "loadSkirmishAILibrary() done");
	return mySSkirmishAILibrary;
}
/**
* Unloads the specified Skirmish AI.
*
* @return     0: ok
*          != 0: error
*/
EXPORT(int) 
unloadSkirmishAILibrary(const char* const shortName, const char* const version)
{
	simpleLog_log("unloadSkirmishAILibrary()");
	return 0;
}
/**
* @brief       unloads all AIs
* Unloads all AI libraries currently loaded through this interface.
*/
EXPORT(int)
unloadAllSkirmishAILibraries() {
	simpleLog_log("unloadAllSkirmishAILibraries()");
	python_unload();
	return 0;
}
