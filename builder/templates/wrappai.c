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
void   (*PYERR_PRINT)()=NULL;
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
void   (*PY_FINALIZE)()=NULL;
const char* (*PY_GETVERSION)()=NULL;
void   (*PY_INITIALIZE)()=NULL;
void   (*_PY_NONESTRUCT)=NULL;

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
#define _Py_NoneStruct         _PY_NONESTRUCT

{% exec import os.path %}
{% for file in ("converter.c", "event_wrapper.c", "command_wrapper.c", "callback.c", ) %}
	{% include os.path.join(templatedir,file) %}
{% endfor %}

static PyObject* wrapper;
static const PyObject* sys_module;

#define LOG simpleLog_log

/*add to search path and load module */
PyObject *pythonLoadModule(const char *modul, const char* path)
{
	PyObject *res=NULL;
	PyObject *tmpname;
	if (path!=NULL){
		LOG("Including Python search path %s", path);
		PyObject* pathlist = PyObject_GetAttrString((PyObject*)sys_module, "path");
		PyList_Append(pathlist, PyString_FromString(path));
	}
	tmpname=PyString_FromString(modul);
	res=PyImport_Import(tmpname);
	if (!res){
		LOG("Could not load python module %s\"%s\"",path,modul);
		PyErr_Print();
		return res;
	}
	LOG("Loaded Python Module %s in %s",modul, path);
	Py_DECREF(tmpname);
	return res;
}


EXPORT(int)
python_handleEvent(int teamId, int topic, const void* data)
{
	PyObject * pfunc;
	PyObject * args;
	if (wrapper==NULL){
	    //FIXME we should return -1 here but spring then doesn't allow an /aireload command
	    return 0;
	}
	pfunc=PyObject_GetAttrString((PyObject*)wrapper,PYTHON_INTERFACE_HANDLE_EVENT);
	if (!pfunc){
		LOG("failed to extract function from module");
	return -1;
	}
	args = Py_BuildValue("(iiO)",teamId, topic, event_convert(topic,(void*)data));
	if (!args){
	    LOG("failed to build args");
	    return -1;
	}
	PyObject_CallObject(pfunc, args);
	Py_DECREF(pfunc);
	return 0;
}

/* Initialize the AI for team teamId */
EXPORT(int)
python_init(int teamId, const struct SSkirmishAICallback* aiCallback)
{
	LOG("python_init()");
	const char* className = aiCallback->Clb_SkirmishAI_Info_getValueByKey(teamId,
			PYTHON_SKIRMISH_AI_PROPERTY_CLASS_NAME);
	LOG("Name of the AI: %s",className);
	const char* modName = aiCallback->Clb_SkirmishAI_Info_getValueByKey(teamId,
			PYTHON_SKIRMISH_AI_PROPERTY_MODULE_NAME);
	LOG("Python Class Name: %s",modName);

	const char* aipath = aiCallback->Clb_DataDirs_getConfigDir(teamId);
	PyObject* aimodule = pythonLoadModule(modName, aipath);	
	if (!aimodule)
		return -1;

	
	PyObject* class = PyObject_GetAttrString(aimodule, className);
	if (!class)
		return -1;
	
	PyObject* classlist = PyObject_GetAttrString((PyObject*)wrapper, "aiClasses");
	if (!classlist)
		return -1;

	if (PyType_Ready(&PyAICallback_Type) < 0){
		LOG("Error PyType_Ready()");
		PyErr_Print();
		return -1;
	}
	return PyDict_SetItem(classlist, PyInt_FromLong(teamId), class);
}

/*release an ai*/
EXPORT(int)
python_release(int teamId)
{
	LOG("python_release()");
	Py_Finalize();
	return 0;
}

void bindAndLoadPython(){
	void *hPython=sharedLib_load("/usr/lib/libpython2.6.so");
	PYDICT_GETITEMSTRING=sharedLib_findAddress(hPython, "PyDict_GetItemString");
	PY_BUILDVALUE=sharedLib_findAddress(hPython, "Py_BuildValue");
	PYDICT_SETITEM=sharedLib_findAddress(hPython, "PyDict_SetItem");
	PYERR_PRINT=sharedLib_findAddress(hPython, "PyErr_Print");
	PYFLOAT_ASDOUBLE=sharedLib_findAddress(hPython, "PyFloat_AsDouble");
	PYFLOAT_FROMDOUBLE=sharedLib_findAddress(hPython, "PyFloat_FromDouble");
	PYIMPORT_IMPORT=sharedLib_findAddress(hPython, "PyImport_Import");
	PYINT_FROMLONG=sharedLib_findAddress(hPython, "PyInt_FromLong");
	PYLIST_APPEND=sharedLib_findAddress(hPython, "PyList_Append");
	PYLIST_GETITEM=sharedLib_findAddress(hPython, "PyList_GetItem");
	PYLIST_NEW=sharedLib_findAddress(hPython, "PyList_New");
	PYLIST_SETITEM=sharedLib_findAddress(hPython, "PyList_SetItem");
	PYOBJECT_CALLOBJECT=sharedLib_findAddress(hPython, "PyObject_CallObject");
	PYOBJECT_GETATTRSTRING=sharedLib_findAddress(hPython, "PyObject_GetAttrString");
	PYSTRING_FROMSTRING=sharedLib_findAddress(hPython, "PyString_FromString");
	PYTUPLE_GETITEM=sharedLib_findAddress(hPython, "PyTuple_GetItem");
	PYTYPE_READY=sharedLib_findAddress(hPython, "PyType_Ready");
	PY_FINALIZE=sharedLib_findAddress(hPython, "Py_Finalize");
	PY_GETVERSION=sharedLib_findAddress(hPython, "Py_GetVersion");
	PY_INITIALIZE=sharedLib_findAddress(hPython, "Py_Initialize");
	_PY_NONESTRUCT=sharedLib_findAddress(hPython, "_Py_NoneStruct");
}


/*
* Initialize Python
*/
EXPORT (int)
python_load(const struct SAIInterfaceCallback* callback,const int interfaceId, const char* logFileName, bool useTimeStamps, int logLevel)
{
	simpleLog_init(logFileName, useTimeStamps,logLevel, true);
	LOG("python_load()");
	//Initalize Python
	Py_Initialize();
	LOG("Initialized python %s",Py_GetVersion());
	sys_module=pythonLoadModule("sys", NULL);
	if (!sys_module)
		return -1;
	wrapper=pythonLoadModule(PYTHON_INTERFACE_MODULE_NAME,callback->DataDirs_getConfigDir(interfaceId));
	if (!wrapper)
		return -1;
	return 0;
}
