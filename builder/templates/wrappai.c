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

	@author Andreas Löscher
	@author Matthias Ableitner <spam@abma.de>
*/


/* This file was generated {% now %} */

#undef _DEBUG /* Link with python24.lib and not python24_d.lib */
#include <Python.h>
#include "ai.h"


#include "CUtils/SimpleLog.h"
#include "CUtils/SharedLibrary.h"

#include "ExternalAI/Interface/AISCommands.h"
#include "ExternalAI/Interface/SAIFloat3.h"
#include "ExternalAI/Interface/AISEvents.h"
#include "ExternalAI/Interface/SSkirmishAICallback.h"

#include "InterfaceDefines.h"
#include "InterfaceExport.h"

PyObject* PyAICallback_New(const struct SSkirmishAICallback* callback);


// Python functions pointers
void*  (*PYDICT_GETITEMSTRING)(void*, const char*)=NULL;
void*  (*PY_BUILDVALUE)(char*, ...)=NULL;
int    (*PYDICT_SETITEM)(void*, void*, void*)=NULL;
void   (*PYERR_PRINT)(void)=NULL;
double (*PYFLOAT_ASDOUBLE)(void*)=NULL;
void*  (*PYFLOAT_FROMDOUBLE)(double)=NULL;
void*  (*PYIMPORT_IMPORT)(void*)=NULL;
void*  (*PYINT_FROMLONG)(long)=NULL;
int    (*PYLIST_APPEND)(void *, void*)=NULL;
void*  (*PYLIST_GETITEM)(void *,Py_ssize_t)=NULL;
void*  (*PYLIST_NEW)(Py_ssize_t)=NULL;
int    (*PYLIST_SETITEM)(void*, Py_ssize_t, void*)=NULL;
void*  (*PYOBJECT_CALLOBJECT)(void*, void*)=NULL;
void*  (*PYOBJECT_GETATTRSTRING)(void*, const char*)=NULL;
void*  (*PYSTRING_FROMSTRING)(const char*)=NULL;
void*  (*PYTUPLE_GETITEM)(void*, Py_ssize_t)=NULL;
int    (*PYTYPE_READY)(void*)=NULL;
void   (*PY_FINALIZE)(void)=NULL;
const char* (*PY_GETVERSION)(void)=NULL;
void   (*PY_INITIALIZE)(void)=NULL;
PyObject *_PY_NONESTRUCT=NULL;


void* findAddressEx(void *handle, const char *name){
	void* res;
	res=sharedLib_findAddress(handle, name);
	if (res==NULL)
		simpleLog_log("Unable to find adress for %s %p",name, handle);
	return res;
}

void
bindPythonFunctions(void *hPython)
{
	PYDICT_GETITEMSTRING=findAddressEx(hPython, "PyDict_GetItemString");
	PY_BUILDVALUE=findAddressEx(hPython, "Py_BuildValue");
	PYDICT_SETITEM=findAddressEx(hPython, "PyDict_SetItem");
	PYERR_PRINT=findAddressEx(hPython, "PyErr_Print");
	PYFLOAT_ASDOUBLE=findAddressEx(hPython, "PyFloat_AsDouble");
	PYFLOAT_FROMDOUBLE=findAddressEx(hPython, "PyFloat_FromDouble");
	PYIMPORT_IMPORT=findAddressEx(hPython, "PyImport_Import");
	PYINT_FROMLONG=findAddressEx(hPython, "PyLong_FromLong");
	PYLIST_APPEND=findAddressEx(hPython, "PyList_Append");
	PYLIST_GETITEM=findAddressEx(hPython, "PyList_GetItem");
	PYLIST_NEW=findAddressEx(hPython, "PyList_New");
	PYLIST_SETITEM=findAddressEx(hPython, "PyList_SetItem");
	PYOBJECT_CALLOBJECT=findAddressEx(hPython, "PyObject_CallObject");
	PYOBJECT_GETATTRSTRING=findAddressEx(hPython, "PyObject_GetAttrString");
	PYSTRING_FROMSTRING=findAddressEx(hPython, "PyString_FromString");
	PYTUPLE_GETITEM=findAddressEx(hPython, "PyTuple_GetItem");
	PYTYPE_READY=findAddressEx(hPython, "PyType_Ready");
	PY_FINALIZE=findAddressEx(hPython, "Py_Finalize");
	PY_GETVERSION=findAddressEx(hPython, "Py_GetVersion");
	PY_INITIALIZE=findAddressEx(hPython, "Py_Initialize");
	_PY_NONESTRUCT=findAddressEx(hPython, "_Py_NoneStruct");

	if (PYSTRING_FROMSTRING==NULL) //Python 3
		PYSTRING_FROMSTRING=findAddressEx(hPython, "PyUnicode_InternFromString");

}

//Python functions
#define PyDict_GetItemString   PYDICT_GETITEMSTRING
#define Py_BuildValue          PY_BUILDVALUE
#define PyDict_SetItem         PYDICT_SETITEM
#define PyErr_Print            PYERR_PRINT
#define PyFloat_AsDouble       PYFLOAT_ASDOUBLE
#define PyFloat_FromDouble     PYFLOAT_FROMDOUBLE
#define PyImport_Import        PYIMPORT_IMPORT
#define PyInt_FromLong         PYINT_FROMLONG
#define PyList_Append          PYLIST_APPEND
#define PyList_GetItem         PYLIST_GETITEM
#define PyList_New             PYLIST_NEW
#define PyList_SetItem         PYLIST_SETITEM
#define PyObject_CallObject    PYOBJECT_CALLOBJECT
#define PyObject_GetAttrString PYOBJECT_GETATTRSTRING
#define PyString_FromString    PYSTRING_FROMSTRING
#define PyTuple_GetItem        PYTUPLE_GETITEM
#define PyType_Ready           PYTYPE_READY
#define Py_Finalize            PY_FINALIZE
#define Py_GetVersion          PY_GETVERSION
#define Py_Initialize          PY_INITIALIZE
#undef Py_None
#define Py_None		       _PY_NONESTRUCT

{% exec import os.path %}
{% for file in ("converter.c", "event_wrapper.c", "command_wrapper.c", "callback.c", ) %}
	{% include os.path.join(templatedir,file) %}
{% endfor %}

static PyObject* hWrapper;
static const PyObject* hSysModule;

/*add to search path and load module */
PyObject *pythonLoadModule(const char *modul, const char* path)
{
	PyObject *res=NULL;
	PyObject *tmpname;
	if (path!=NULL){
		simpleLog_log("Including Python search path %s", path);
		PyObject* pathlist = PyObject_GetAttrString((PyObject*)hSysModule, "path");
		PyList_Append(pathlist, PyString_FromString(path));
	}
	tmpname=PyString_FromString(modul);
	res=PyImport_Import(tmpname);
	if (!res){
		simpleLog_log("Could not load python module %s\"%s\"",path,modul);
		PyErr_Print();
		return res;
	}
	if (path==NULL)
		simpleLog_log("Loaded Python Module %s in default search path",modul);
	else
		simpleLog_log("Loaded Python Module %s in %s",modul, path);
	Py_DECREF(tmpname);
	return res;
}
/**
* Through this function, the AI receives events from the engine.
* For details about events that may arrive here, see file AISEvents.h.
*
* @param       teamId  the instance of the AI that the event is addressed to
* @param       topic   unique identifyer of a message
*                                      (see EVENT_* defines in AISEvents.h)
* @param       data    an topic specific struct, which contains the data
*                                      associatedwith the event
*                                      (see S*Event structs in AISEvents.h)
* @return     0: ok
*          != 0: error
*/
int CALLING_CONV python_handleEvent(int teamId, int topic, const void* data)
{
	PyObject * pfunc;
	PyObject * args;
	if (hWrapper==NULL){
	    //FIXME we should return -1 here but spring then doesn't allow an /aireload command
	    return 0;
	}
	pfunc=PyObject_GetAttrString((PyObject*)hWrapper,PYTHON_INTERFACE_HANDLE_EVENT);
	if (!pfunc){
		simpleLog_log("failed to extract function from module");
	return -1;
	}
	args = Py_BuildValue("(iiO)",teamId, topic, event_convert(topic,(void*)data));
	if (!args){
	    simpleLog_log("failed to build args");
	    return -1;
	}
	PyObject_CallObject(pfunc, args);
	Py_DECREF(pfunc);
	return 0;
}

/**
* This function is called, when an AI instance shall be created for teamId.
* It is called before the first call to handleEvent() for teamId.
*
* A typical series of events (engine point of view, conceptual):
* [code]
* KAIK.init(1)
* KAIK.handleEvent(EVENT_INIT, InitEvent(1))
* RAI.init(2)
* RAI.handleEvent(EVENT_INIT, InitEvent(2))
* KAIK.handleEvent(EVENT_UPDATE, UpdateEvent(0))
* RAI.handleEvent(EVENT_UPDATE, UpdateEvent(0))
* KAIK.handleEvent(EVENT_UPDATE, UpdateEvent(1))
* RAI.handleEvent(EVENT_UPDATE, UpdateEvent(1))
* ...
* [/code]
*
* This method exists only for performance reasons, which come into play on
* OO languages. For non-OO language AIs, this method can be ignored,
* because using only EVENT_INIT will cause no performance decrease.
*
* [optional]
* An AI not exporting this function is still valid.
*
* @param       teamId        the teamId this library shall create an instance for
* @param       callback      the callback for this Skirmish AI
* @return     0: ok
*          != 0: error
*/
int CALLING_CONV python_init(int teamId, const struct SSkirmishAICallback* aiCallback)
{
	simpleLog_log("python_init()");
	const char* className = aiCallback->Clb_SkirmishAI_Info_getValueByKey(teamId,
			PYTHON_SKIRMISH_AI_PROPERTY_CLASS_NAME);
	simpleLog_log("Name of the AI: %s",className);
	const char* modName = aiCallback->Clb_SkirmishAI_Info_getValueByKey(teamId,
			PYTHON_SKIRMISH_AI_PROPERTY_MODULE_NAME);
	simpleLog_log("Python Class Name: %s",modName);

	const char* aipath = aiCallback->Clb_DataDirs_getConfigDir(teamId);
	PyObject* aimodule = pythonLoadModule(modName, aipath);	
	if (!aimodule)
		return -1;

	
	PyObject* class = PyObject_GetAttrString(aimodule, className);
	if (!class)
		return -1;
	
	PyObject* classlist = PyObject_GetAttrString((PyObject*)hWrapper, "aiClasses");
	if (!classlist)
		return -1;

	if (PyType_Ready(&PyAICallback_Type) < 0){
		simpleLog_log("Error PyType_Ready()");
		PyErr_Print();
		return -1;
	}
	return PyDict_SetItem(classlist, PyInt_FromLong(teamId), class);
}
/**
* This function is called, when an AI instance shall be deleted.
* It is called after the last call to handleEvent() for teamId.
*
* A typical series of events (engine point of view, conceptual):
* [code]
* ...
* KAIK.handleEvent(EVENT_UPDATE, UpdateEvent(654321))
* RAI.handleEvent(EVENT_UPDATE, UpdateEvent(654321))
* KAIK.handleEvent(EVENT_UPDATE, UpdateEvent(654322))
* RAI.handleEvent(EVENT_UPDATE, UpdateEvent(654322))
* KAIK.handleEvent(EVENT_RELEASE, ReleaseEvent(1))
* KAIK.release(1)
* RAI.handleEvent(EVENT_RELEASE, ReleaseEvent(2))
* RAI.release(2)
* [/code]
*
* This method exists only for performance reasons, which come into play on
* OO languages. For non-OO language AIs, this method can be ignored,
* because using only EVENT_RELEASE will cause no performance decrease.
*
* [optional]
* An AI not exporting this function is still valid.
*
* @param       teamId  the teamId the library shall release the instance of
* @return     0: ok
*          != 0: error
*/
int CALLING_CONV python_release(int teamId)
{
	//TODO: call python-release function
	simpleLog_log("python_release()");
	return 0;
}

/*
 * Initialize the Python Interpreter
 * @return 0 on success
 */
int python_load(const struct SAIInterfaceCallback* callback,const int interfaceId)
{
	simpleLog_log("python_load()");
	//Initalize Python
	Py_Initialize();
	simpleLog_log("Initialized python %s",Py_GetVersion());
	hSysModule=pythonLoadModule("sys", NULL);
	if (!hSysModule)
		return -1;
	hWrapper=pythonLoadModule(PYTHON_INTERFACE_MODULE_NAME,callback->DataDirs_getConfigDir(interfaceId));
	if (!hWrapper)
		return -1;

	return 0;
}

/*
 * Unload the Python Interpreter
 */
void python_unload(void){
	simpleLog_log("python_unload()");
	Py_Finalize();
	hWrapper=NULL;
	hSysModule=NULL;
}
