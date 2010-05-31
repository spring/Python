# -*- coding: utf-8 -*-
callback=None
commander=0
moved=False
myteamId=0

from PyAI.interface import *
from PyAI import Team
from PyAI import BaseAI
import PyAI
import sys, traceback

aiClasses = {}

ais = {} # {team -> {event -> function}}

def handleEvent(teamId, topic, data):
	try:
		if (topic==1):
			team = Team(teamId, data["callback"])
			if aiClasses.has_key(teamId):
				ais[teamId]={}
				aiClasses[teamId](team, {"ais":ais})
				if ais[teamId].has_key(PyAI.EVENT_INIT):
					ais[teamId][PyAI.EVENT_INIT](data)
			else:
				return -1
		elif ais.has_key(teamId) and ais[teamId].has_key(topic):
			ais[teamId][topic](data)
	except Exception, e:
		traceback.print_exception(sys.exc_type, sys.exc_value,sys.exc_traceback)
