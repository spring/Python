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
		self.frame=-1
		self.units = {}
		self.bindFunction(self.eventUnitCreated, PyAI.EVENT_UNIT_CREATED)
		self.bindFunction(self.eventInit, PyAI.EVENT_INIT)
		self.bindFunction(self.eventUpdate, PyAI.EVENT_UPDATE)
		self.bindFunction(self.eventRelease, PyAI.EVENT_RELEASE)

	def eventUnitCreated(self, data):
		print("Unit created (unit builder)", self.frame, data["unit"], data["builder"])
		self.units[data["unit"]]  = data["unit"] 

	def eventRelease(self, data):
		print("eventRelease")

	def eventInit(self,data):
		print("eventInit", self.frame)
		self.units = {}
		print("Map width: ", Map.getWidth(), " Height: ", Map.getHeight())
		
	def cheatInit(self):
		#Cheat start unit
		print("cheatInit")
		if (len(self.units)>0): #only cheat when no units are avaiable
			return
		Cheats.setEnabled(True)
		Command.giveMeNewUnitCheat(UnitDef.getUnitDefByName("armcom"), Map.getStartPos())
		
		print(Resource.getCount())
		for i in xrange(Resource.getCount()):
			print(i, Resource.getName(i))
			Command.giveMeResourceCheat(i,1000)

	def eventUpdate(self,data):
		if (self.frame == -1):
			print("eventUpdate", data["frame"])
			self.initFrame=data["frame"]+1
		if (self.frame==self.initFrame): #process initCreate Events, then cheatInit
			self.cheatInit()
		self.frame=data["frame"]

