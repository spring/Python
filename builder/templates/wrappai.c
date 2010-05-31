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

#include "ExternalAI/Interface/AISCommands.h"
#include "ExternalAI/Interface/SAIFloat3.h"
#include "ExternalAI/Interface/AISEvents.h"
#include "ExternalAI/Interface/SSkirmishAICallback.h"

#include "InterfaceDefines.h"
#include "CUtils/SimpleLog.h"


{% exec import os.path %}
{% for file in ("converter.c", "event_wrapper.c", "command_wrapper.c", "callback.c", ) %}
	{% include os.path.join(templatedir,file) %}
{% endfor %}

static PyObject* wrapper;
static const PyObject* sys_module;

/*add path to the python module search path*/
int update_python_path(const char* path)
{
	simpleLog_log("update_python_path() %s", path);
	PyObject* pathlist = PyObject_GetAttrString((PyObject*)sys_module, "path");
	return PyList_Append(pathlist, PyString_FromString(path));
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

/* Initialize the AI for team teamId */
EXPORT(int)
python_init(int teamId, const struct SSkirmishAICallback* aiCallback)
{
	simpleLog_log("python_init()");
	const char* className = aiCallback->Clb_SkirmishAI_Info_getValueByKey(teamId,
			PYTHON_SKIRMISH_AI_PROPERTY_CLASS_NAME);
	simpleLog_log("classname %s",className);
	const char* modName = aiCallback->Clb_SkirmishAI_Info_getValueByKey(teamId,
			PYTHON_SKIRMISH_AI_PROPERTY_MODULE_NAME);
	simpleLog_log("modName %s",modName);

	const char* aipath = aiCallback->Clb_DataDirs_getConfigDir(teamId);
	update_python_path(aipath);
	if (className == NULL) {
		simpleLog_log("Couldn't find className");
                return -1;
	}
	PyObject* tmpname = PyString_FromString(modName);
	PyObject* aimodule = PyImport_Import(tmpname);

	Py_DECREF(tmpname);
	if (!aimodule){
		simpleLog_log("python_init() failed:");
		PyErr_Print();
		wrapper=NULL;
		return -1;
	}

	
	PyObject* class = PyObject_GetAttrString(aimodule, className);
	if (!class)
		return -1;
	
	PyObject* classlist = PyObject_GetAttrString((PyObject*)wrapper, "aiClasses");
	if (!classlist)
		return -1;

	if (PyType_Ready(&PyAICallback_Type) < 0){
		simpleLog_log("Error PyType_Ready()");
		PyErr_Print();
		return -1;
	}
	return PyDict_SetItem(classlist, PyInt_FromLong(teamId), class);
}

/*release an ai*/
EXPORT(int)
python_release(int teamId)
{
	simpleLog_log("python_release()");
	Py_Finalize();
	return 0;
}

/*
* Initialize Python
*/

EXPORT (int)
python_load(const struct SAIInterfaceCallback* callback,const int interfaceId)
{
	PyObject *tmpname;
	simpleLog_log("python_load()");
	
	//Initalize Python
	Py_Initialize();
	simpleLog_log("Initialized python %s",Py_GetVersion());
	
	sys_module=PyImport_Import(PyString_FromString("sys"));
	
	
	if (!sys_module)
	{
		simpleLog_log("Could not load sys module");
		PyErr_Print();
		return -1;
	}
	simpleLog_log("sys module loaded");

	if (update_python_path(callback->DataDirs_getConfigDir(interfaceId)))
	{
		simpleLog_log("Could not update python path for wrapper");
		PyErr_Print();
		return -1;
	}
	tmpname=PyString_FromString(PYTHON_INTERFACE_MODULE_NAME);
	wrapper=PyImport_Import(tmpname);
	Py_DECREF(tmpname);
	if (!wrapper)
	{
		simpleLog_log("Could not load interface module %s",PYTHON_INTERFACE_MODULE_NAME);
		PyErr_Print();
		return -1;
	}
	simpleLog_log("interface module module loaded");
	return 0;
}

