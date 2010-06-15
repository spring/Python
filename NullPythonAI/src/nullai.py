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
from PyAI import Command
from PyAI import UnitDef
from PyAI import Map, Cheats, Resource

class NullPythonAI(BaseAI):
	def __init__(self, team, pyclb):
		super(self.__class__, self).__init__(team, pyclb)
		self.frame=-1
		self.bindFunction(self.eventUnitCreated, PyAI.EVENT_UNIT_CREATED)
		self.bindFunction(self.eventInit, PyAI.EVENT_INIT)
		self.bindFunction(self.eventUpdate, PyAI.EVENT_UPDATE)
		self.bindFunction(self.eventRelease, PyAI.EVENT_RELEASE)
		
		self.units = {}
		self.command = None
		self.unitdef = None
		self.resource = None
	def eventUnitCreated(self, data):
		print "Unit created (unit builder)", self.frame, data["unit"], data["builder"]
		self.units[data["unit"]]  = data["unit"]

	def eventRelease(self, data):
		print "eventRelease"
	def eventInit(self,data):
		print "eventInit", self.frame
		self.units = {}
		self.command = Command(self.team)
		self.unitdef = UnitDef(self.team)
		self.resource = Resource(self.team)
		self.map = Map(self.team)
		print "Map width: ", self.map.getWidth(), " Height: ", self.map.getHeight()
		
	def cheatInit(self):
		#Cheat start unit
		print "cheatInit"
		if (len(self.units)>0): #only cheat when no units are avaiable
			return
		self.cheats = Cheats(self.team)
		self.cheats.setEnabled(True)
		self.command.giveMeNewUnitCheat(self.unitdef.getUnitDefByName("armcom"), self.map.getStartPos())
		
		print self.resource.getCount()
		for i in xrange(self.resource.getCount()):
			print i, self.resource.getName(i)
			self.command.giveMeResourceCheat(i,1000)

	def eventUpdate(self,data):
		if (self.frame == -1):
			print "eventUpdate", data["frame"]
			self.initFrame=data["frame"]+1
		if (self.frame==self.initFrame): #process initCreate Events, then cheatInit
			self.cheatInit()
		self.frame=data["frame"]

