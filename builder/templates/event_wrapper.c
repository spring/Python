static PyObject* 
event_convert(int topic, void* data)
{
  switch (topic) {
    {% for event in events %}
    case {{event}}:
      return {{events[event]}};
    {% endfor %}
  }
  return NULL;
}
/* End Event Wrapper */