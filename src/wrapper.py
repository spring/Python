# -*- coding: utf-8 -*-
callback=None
commander=0
moved=False
myteamId=0

import PyAI

from PyAI.interface import *
from PyAI import Team
from PyAI import BaseAI

import sys, traceback

aiClasses = {}	# {teamId:Class}
ais       = {}	# {teamId : ({event : function}, team)}
teams     = {}	# {teamId : team }


def handleEvent(teamId, topic, data):
	try:
		if topic == PyAI.EVENT_INIT:
			team = Team(teamId, data["callback"])
			teams[teamId] = team
			if aiClasses.has_key(teamId):
				ais[teamId]={}
				useTeam(teamId)
				aiClasses[teamId](team, {"ais":ais})

			else:
				return -1

		if ais.has_key(teamId) and ais[teamId].has_key(topic):
			useTeam(teamId)
			ais[teamId][topic](data)

	except:
		traceback.print_exception(sys.exc_type, sys.exc_value,sys.exc_traceback)


def useTeam(teamId):
	PyAI.team._currentTeam = teams[teamId]
