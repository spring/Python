# -*- coding: utf-8 -*-
#
#	Copyright 2010  Andreas Löscher
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

import PyAI

from PyAI import BaseAI
from PyAI import UnitDef, Map, Cheats, Resource, Command


class NullPythonAI(BaseAI):
	""" Example AI"""
	def __init__(self, team, pyclb):
		super(NullPythonAI, self).__init__(team, pyclb)
		self.bindFunction(self.eventInit, PyAI.EVENT_INIT)

	def eventInit(self,data):
		print("eventInit")
		print("Map width: ", Map.getWidth(), " Height: ", Map.getHeight())
		
