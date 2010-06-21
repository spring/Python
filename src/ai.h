/*
	Copyright 2008  Nicolas Wu

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

#ifndef _AIEXPORT_H
#define _AIEXPORT_H

#include "ExternalAI/Interface/aidefines.h"
#include "ExternalAI/Interface/SAIInterfaceCallback.h"
#include "ExternalAI/Interface/SSkirmishAICallback.h"

int CALLING_CONV python_init(int teamId, const struct SSkirmishAICallback* aiCallback);
int CALLING_CONV python_release(int teamId);
int CALLING_CONV python_handleEvent(int teamId, int topic, const void* data);
int python_load(const struct SAIInterfaceCallback* callback, int interfaceId);
void python_unload(void);

#endif // _AIEXPORT_H
