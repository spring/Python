static int*
build_intarray(PyObject* list)
{
  Py_ssize_t n=PyList_GET_SIZE(list);
  int* array=malloc(sizeof(int)*(long)n);
  Py_ssize_t i;
  for (i=0;i<n;i++)
  {
    array[i]=(int)PyInt_AS_LONG(PyList_GetItem(list, i));
  }
  return array;
}

static PyObject* 
convert_SAIFloat3(struct SAIFloat3* value)
{
  return Py_BuildValue("(fff)", value->x,
                                value->y,
                                value->z);
}

static PyObject*
convert_intarray(int* unitIds, int numUnitIds)
{
  int i;
  PyObject* list=PyList_New(numUnitIds);
  for (i=0;i<numUnitIds;i++)
  {
    PyList_SetItem(list, i, PyInt_FromLong((long)unitIds[i]));
  }
  return list;
}

