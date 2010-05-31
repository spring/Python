/* wrapper for command struct's */

static struct SAIFloat3*
build_SAIFloat3(PyObject* tpl)
{
	struct SAIFloat3* data=malloc(sizeof(struct SAIFloat3));
	data->x=PyFloat_AsDouble(PyTuple_GetItem(tpl, 0));
	data->y=PyFloat_AsDouble(PyTuple_GetItem(tpl, 1));
	data->z=PyFloat_AsDouble(PyTuple_GetItem(tpl, 2));
	return data;
}

void*
command_convert(int commandTopic, PyObject* command)
{
	void *data=NULL;
	switch (commandTopic) {
	{% for command in commands %}
		case {{command}}:
		{% exec cmd=commands[command] %}
		{% include os.path.join(templatedir, "create_command.c") %}
		break;
	{% endfor %}
	}
	return data;
}

PyObject*
command_reverse(int topic, void* data)
{
	switch (topic) {
	{% for command in commands %}
	{% exec structname="struct "+commands[command][0] %}
	{% exec members = commands[command][1] %}
	{% for member in members %}
	{% if "ret_" in member %}
		case {{command}}:
			return {{converter(members[member], "(("+structname+"*)data)->"+member)}};
	{% endif %}
	{% endfor %}
	{% endfor %}
	}
	return Py_None;
}