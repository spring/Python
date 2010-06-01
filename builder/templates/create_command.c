{% exec structname="struct "+cmd[0] %}
        data = malloc(sizeof({{structname}}));
{% for member in cmd[1] %}
{% exec member, type=member %}
{% if "int*" in type %}
        (({{structname}}*)data)->{{member}} = build_intarray(PyDict_GetItemString(command, "{{member}}"));
{% endif %}

{% if ("int" in type) and not ("int*" in type) %}
        (({{structname}}*)data)->{{member}} = PyInt_AS_LONG(PyDict_GetItemString(command, "{{member}}"));
{% endif %}

{% if "char" in type %}
        (({{structname}}*)data)->{{member}} = PyString_AS_STRING(PyDict_GetItemString(command, "{{member}}"));
{% endif %}
{% if "bool" in type %}
        (({{structname}}*)data)->{{member}} = (bool)PyInt_AS_LONG(PyDict_GetItemString(command, "{{member}}"));
{% endif %}
{% if "SAIFloat3" in type %}
        (({{structname}}*)data)->{{member}} = *(build_SAIFloat3(PyDict_GetItemString(command, "{{member}}")));
{% endif %}

{% endfor %}