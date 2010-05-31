import re, sys

def is_iterable(x):
    try:
        iter(x)
    except TypeError:
        return False
    else:
        return True

smart_split_re = re.compile(r"""
    ([^\s"]*"(?:[^"\\]*(?:\\.[^"\\]*)*)"\S*|
     [^\s']*'(?:[^'\\]*(?:\\.[^'\\]*)*)'\S*|
     \S+)""", re.VERBOSE)

def smart_split(text):
    text = force_unicode(text)
    for bit in smart_split_re.finditer(text):
        yield bit.group(0)

def unescape_string_literal(s):
    if s[0] not in "\"'" or s[-1] != s[0]:
        raise ValueError("Not a string literal: %r" % s)
    quote = s[0]
    return s[1:-1].replace(r'\%s' % quote, quote).replace(r'\\', '\\')

def curry(_curried_func, *args, **kwargs):
    def _curried(*moreargs, **morekwargs):
        return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
    return _curried

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)

def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]
    
def groupby(iterable, keyfunc=None):
    """
    Taken from http://docs.python.org/lib/itertools-functions.html
    """
    if keyfunc is None:
        keyfunc = lambda x:x
    iterable = iter(iterable)
    l = [iterable.next()]
    lastkey = keyfunc(l[0])
    for item in iterable:
        key = keyfunc(item)
        if key != lastkey:
            yield lastkey, l
            lastkey = key
            l = [item]
        else:
            l.append(item)
    yield lastkey, l