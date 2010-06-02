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
