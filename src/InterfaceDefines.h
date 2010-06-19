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

#ifndef _INTERFACEDEFINES_H
#define _INTERFACEDEFINES_H

#ifdef __cplusplus
extern "C" {
#endif

#define PYTHON_SKIRMISH_AI_PROPERTY_CLASS_NAME "className"
#define PYTHON_SKIRMISH_AI_PROPERTY_MODULE_NAME "modName"

#define MY_LOG_FILE                     "interface-log.txt"
#define PYTHON_INTERFACE_MODULE_NAME    "wrapper"
#define PYTHON_INTERFACE_HANDLE_EVENT	"handleEvent"

#define FILEPATH_MAXSIZE                1024

#include <stddef.h> // for NULL

#ifdef __cplusplus
} // extern "C"
#endif

#endif // _INTERFACEDEFINES_H
