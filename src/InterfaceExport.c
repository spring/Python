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

typedef int (*INIT_FUNC)(int teamId, const struct SSkirmishAICallback* aiCallback);
typedef int (*RELEASE_FUNC)(int teamId);
typedef int (*LOAD_FUNC)(const struct SAIInterfaceCallback* callback, int interfaceId,  const char* logFileName, bool useTimeStamps,
		int logLevel);
typedef int (*HANDLE_FUNC)(int teamId, int topic, const void* data);

INIT_FUNC    PYTHON_INIT;
LOAD_FUNC    PYTHON_LOAD;
RELEASE_FUNC PYTHON_RELEASE;
HANDLE_FUNC  PYTHON_HANDLEEVENT;


void* hPythonInterface;
#ifdef WIN32
#define PATH_SEPERATOR "\\"
#else
#define PATH_SEPERATOR "/"
#endif
int loadPythonInterpreter(const char* logFileName, bool useTimeStamps, int logLevel){
	char filename[FILEPATH_MAXSIZE];
	char logBuf[FILEPATH_MAXSIZE];
	const char* const dd_r =
		callback->AIInterface_Info_getValueByKey(interfaceId,
		AI_INTERFACE_PROPERTY_DATA_DIR);
	char absoluteLibPpath[FILEPATH_MAXSIZE];
	//create platform independant libname (.dll, .so, ...)
	sharedLib_createFullLibName(PYTHON_LOADER,(char *)&filename,FILEPATH_MAXSIZE);
	//create absolute lib name
	snprintf(absoluteLibPpath, FILEPATH_MAXSIZE,"%s%s%s",dd_r,PATH_SEPERATOR, filename);
	simpleLog_log("Loading %s",absoluteLibPpath);
	hPythonInterface=sharedLib_load(absoluteLibPpath);
	if (hPythonInterface == NULL){
		snprintf(logBuf,FILEPATH_MAXSIZE,"Error loading python_loader: %s, is python installed?",absoluteLibPpath);
		callback->Log_exception(interfaceId,(char*)&logBuf,0,true);
		return 0; //TODO return -1 when engine supports this
	}
	PYTHON_INIT=(INIT_FUNC)sharedLib_findAddress(hPythonInterface, "python_init");
	PYTHON_RELEASE=(RELEASE_FUNC)sharedLib_findAddress(hPythonInterface, "python_release");
	PYTHON_LOAD=(LOAD_FUNC)sharedLib_findAddress(hPythonInterface, "python_load");
	PYTHON_HANDLEEVENT=(HANDLE_FUNC)sharedLib_findAddress(hPythonInterface, "python_handleEvent");
	if (!(PYTHON_INIT || PYTHON_RELEASE || PYTHON_LOAD || PYTHON_HANDLEEVENT)){
		snprintf(logBuf,FILEPATH_MAXSIZE,"error binding function()");
		callback->Log_exception(interfaceId,(char*)&logBuf,0,true);
		return 0; //TODO return -1 when engine supports this
	}
	simpleLog_log("Python loader successfully loaded, trying to load the python interpreter...");
	PYTHON_LOAD(callback,interfaceId, logFileName, useTimeStamps, logLevel);
	return 0;
}

/*
* opens the log file and tries to load an python interpreter and initalizes
* the basic stuff, the ai is then loaded in 
*
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
		simpleLog_init(logFilePath, useTimeStamps, logLevel);
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
	simpleLog_log("Using log file: %s", propFilePath);
	simpleLog_log("Loading Python");
	int res=loadPythonInterpreter(logFilePath, useTimeStamps, logLevel);
	FREE(logFile);
	return res;
}

EXPORT(int)
releaseStatic()
{
	simpleLog_log("releaseStatic()");
	// release Python part of the interface
	if (hPythonInterface!=NULL)
		PYTHON_RELEASE(0); //TODO FIXME: Teamid is currently unused!

	// release C part of the interface
	util_finalize();
	return 0;
}

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

int CALLING_CONV proxy_skirmishAI_init(int teamId, const struct SSkirmishAICallback* aiCallback) {
	int ret;
	if (PYTHON_INIT==NULL){ //TODO: remove when Log_exception works
		simpleLog_log("proxy_skirmishAI_init(): python wasn't initalized!");
		return 0;
	}
        ret = PYTHON_INIT(teamId, aiCallback);
	if (ret) {
                simpleLog_log("could not load skirmish ai");
                return 0; //FIXME aireload should always work to make developing easy
	}
	simpleLog_log("proxy_skirmishAI_init()");
	return 0;
}

int CALLING_CONV proxy_skirmishAI_release(int teamId)
{
	if (PYTHON_RELEASE==NULL){ //TODO: remove when Log_exception works
		simpleLog_log("proxy_skirmishAI_release(): python wasn't initalized!");
		return 0;
	}
	simpleLog_log("proxy_skirmishAI_release()");
	return PYTHON_RELEASE(teamId);
}

int outputLogCount=0;

int CALLING_CONV proxy_skirmishAI_handleEvent(
		int teamId, int topic, const void* data)
{
	if (PYTHON_RELEASE==NULL){ //TODO: remove when Log_exception works
		if (outputLogCount<5){
			outputLogCount++;
			simpleLog_log("proxy_skirmishAI_handleEvent(): python wasn't initalized!");
		}else if (outputLogCount==5){
			outputLogCount++;
			simpleLog_log("proxy_skirmishAI_handleEvent(): suppressed: python wasn't initalized!");
		}
		return 0;
	}
	return PYTHON_HANDLEEVENT(teamId, topic, data);
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

		mySSkirmishAILibrary->init = &proxy_skirmishAI_init;
		mySSkirmishAILibrary->release = &proxy_skirmishAI_release;
		mySSkirmishAILibrary->handleEvent = &proxy_skirmishAI_handleEvent;
	}
	simpleLog_logL(SIMPLELOG_LEVEL_FINE, "loadSkirmishAILibrary() done");
	return mySSkirmishAILibrary;
}

EXPORT(int) 
unloadSkirmishAILibrary(const char* const shortName, const char* const version)
{
	simpleLog_log("unloadSkirmishAILibrary()");
        releaseStatic();
	return 0;
}

EXPORT(int)
unloadAllSkirmishAILibraries() {
	// TODO FIXME what is the difference from the function above
	simpleLog_log("unloadAllSkirmishAILibraries()");
        releaseStatic();
	return 0;
}
