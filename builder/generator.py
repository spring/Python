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

import sys
import os

from callback_parser import getcallback_functions
from event_parser import getevents, getcommands, parse_enums
from interface_builder import buildclasses, commandfuncs

from helper import converter

from template import Template


PATH = os.path.join("ExternalAI","Interface")

CALLBACKFILE = os.path.join(PATH,"SSkirmishAICallback.h")
EVENTFILE = os.path.join(PATH,"AISEvents.h")
COMMANDFILE = os.path.join(PATH, "AISCommands.h")

TEMPLATEDIR = None

class Generator(object):
  def __init__(self, templatedir, springdir, outputdir, options=()):
    self.templatedir=templatedir
    self.springdir=springdir
    self.outputdir=outputdir
    
    files = [CALLBACKFILE, EVENTFILE, COMMANDFILE]
    for i, f in enumerate(files):
      files[i]=os.path.join(springdir,f)

    self.clbfuncs, plainfuncs = getcallback_functions(files[0])
    self.classes= buildclasses(plainfuncs)
    self.events = getevents(files[1])
    self.commands = getcommands(files[2])
    self.command_types = parse_enums(files[2])
    self.event_types = parse_enums(files[1])
    self.commandfuncs = commandfuncs(self.commands)
    
    
    self.options = set(options)
    
  def render(self):
    # render wrapper for handleEvent and callback functions
    out = os.path.join(self.outputdir, "ai.c")
    tempfile = os.path.join(self.templatedir, "wrappai.c")
    template = open(tempfile, "r")
    
    
    stream = Template(template.read()).render({'clbfuncs'    : self.clbfuncs,
                                               'events'      : self.events,
                                               'commands'    : self.commands,
                                               'templatedir' : self.templatedir,
                                               'converter'   : converter,
                                               'options'     : self.options
                                              })
    template.close()
    outfile = open(out, "w")
    outfile.write(stream)
    outfile.close()
    
    # render interface
    out = os.path.join(self.outputdir, "PyAI", "interface.py")
    tempfile = os.path.join(self.templatedir, "aiInterface.py")
    template = open(tempfile, "r")
    
    stream = Template(template.read()).render({'classes'     : self.classes,
                                               'commands'    : self.commandfuncs,
                                               'cmd_types'   : self.command_types,
                                               'evt_types'   : self.event_types,
                                               'options'     : self.options
                                              })
    outfile = open(out, "w")
    outfile.write(stream)
    outfile.close()

if __name__=='__main__':
  if (len(sys.argv) != 4):
    print 'Usage: '+sys.argv[0]+' springdir templatedir outputdir '
    sys.exit(-1)
  springdir=os.path.expanduser(sys.argv[1]+'/rts')
  templatedir=os.path.expanduser(sys.argv[2])
  outputdir=os.path.expanduser(sys.argv[3])
  fullpath=outputdir+"/PyAI"
  if (not os.path.exists(fullpath)):
    os.makedirs(fullpath)
  print "Generating Sources..."
  Generator(templatedir,springdir,outputdir).render()
  print "done"
