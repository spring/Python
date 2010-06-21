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

class BaseAI(object):
	def __init__(self, team, clb):
		super(BaseAI, self).__init__()
		self.team = team
		self._ais = clb["ais"]
	def bindFunction(self, function, event):
		""" binds a function for one team to an event
		"""
		assert self._ais.has_key(self.team.teamId), "team not found"
		assert isinstance(event, int), "wrong event type"
		self._ais[self.team.teamId][event] = function
	def __repr__(self):
		return "<"+self.__class__.__name__ + " instance with team: " + repr(self.team) +">"