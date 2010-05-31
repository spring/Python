typedef struct {
  PyObject_HEAD;
  const struct SSkirmishAICallback* callback; // C Callback Object
} PyAICallbackObject;

static PyTypeObject PyAICallback_Type;

PyObject*
PyAICallback_New(const struct SSkirmishAICallback* callback)
{
  PyAICallbackObject *self;
  self = (PyAICallbackObject *)PyAICallback_Type.tp_alloc(&PyAICallback_Type, 0);
  
  if (self)
  {
    self->callback=callback;
  }
  return (PyObject*)self;
}

{% for funcname in clbfuncs %}
PyObject*
{{funcname}}(PyObject* ob, PyObject* args)
{
  {{clbfuncs[funcname]}}
}
{% endfor %}

static PyMethodDef callback_methods[] = {
{% for funcname in clbfuncs %}
     {"{{funcname}}", (PyCFunction){{funcname}}, METH_VARARGS, "{{funcname}}" },
{% endfor %}
    {NULL}  /* Sentinel */
};

static PyTypeObject PyAICallback_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "PyAICallback",            /*tp_name*/
    sizeof(PyAICallbackObject),/*tp_basicsize*/
    0,                         /*tp_itemsize*/
    0,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "callback object",           /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    callback_methods,             /* tp_methods */
};