# -*- coding: utf-8 -*-

# This file was generated {% now %}

def dict_helper(vals, keys):
	i = len(vals)
	assert i==len(keys)
	for i, v in enumerate(vals):
		yield (keys[i],v)

{% for cmd in cmd_types %}
{{cmd}}={{str(cmd_types[cmd])}}
{% endfor %}

NUM_CMD_TOPICS = {{len(cmd_types)}}

{% for evt in evt_types %}
{{evt}}={{str(evt_types[evt])}}
{% endfor %}

NUM_EVENTS = {{len(evt_types)}}

{% for classname in classes %}
class {{classname}}(object):
  def __init__(self, team):
    self.callback=team.callback
    self.teamId=team.teamId
{% for function in classes[classname] %}
{{function}}
{% endfor %}

{% endfor %}

class Command(object):
  def __init__(self, team):
    self.callback = team.callback
    self.teamId = team.teamId
    self.id=0
{% for function in commands %}
{{commands[function]}}
{% endfor %}