"""Default tags used by the template system, available to all templates."""

import sys
import re
from itertools import cycle as itertools_cycle
try:
    reversed
except NameError:
    from django.utils.itercompat import reversed     # Python 2.3 fallback

from engine import Node, NodeList, Template, Context
from engine import TemplateSyntaxError, VariableDoesNotExist, BLOCK_TAG_START, BLOCK_TAG_END, VARIABLE_TAG_START, VARIABLE_TAG_END, SINGLE_BRACE_START, SINGLE_BRACE_END, COMMENT_TAG_START, COMMENT_TAG_END
from engine import get_library, Library, InvalidTemplateLibrary
from helper import groupby
from engine import Template

register = Library()

class NowNode(Node):
    def render(self, context):
        """ rewritten to not include more code """
        import time
        lc = time.localtime(time.time())
        return str(lc[0])+"-"+str(lc[1])+"-"+str(lc[2])+" "+str(lc[3])+":"+str(lc[3])+":"+str(lc[5])

#@register.tag
def now(parser, token):
    return NowNode()
now = register.tag(now)

class TemplateTagNode(Node):
    mapping = {'openblock': BLOCK_TAG_START,
               'closeblock': BLOCK_TAG_END,
               'openvariable': VARIABLE_TAG_START,
               'closevariable': VARIABLE_TAG_END,
               'openbrace': SINGLE_BRACE_START,
               'closebrace': SINGLE_BRACE_END,
               'opencomment': COMMENT_TAG_START,
               'closecomment': COMMENT_TAG_END,
               }

    def __init__(self, tagtype):
        self.tagtype = tagtype

    def render(self, context):
        return self.mapping.get(self.tagtype, '')

#@register.tag
def templatetag(parser, token):
    """
    Outputs one of the bits used to compose template tags.

    Since the template system has no concept of "escaping", to display one of
    the bits used in template tags, you must use the ``{% templatetag %}`` tag.

    The argument tells which template bit to output:

        ==================  =======
        Argument            Outputs
        ==================  =======
        ``openblock``       ``{%``
        ``closeblock``      ``%}``
        ``openvariable``    ``{{``
        ``closevariable``   ``}}``
        ``openbrace``       ``{``
        ``closebrace``      ``}``
        ``opencomment``     ``{#``
        ``closecomment``    ``#}``
        ==================  =======
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError, "'templatetag' statement takes one argument"
    tag = bits[1]
    if tag not in TemplateTagNode.mapping:
        raise TemplateSyntaxError("Invalid templatetag argument: '%s'."
                                  " Must be one of: %s" %
                                  (tag, TemplateTagNode.mapping.keys()))
    return TemplateTagNode(tag)
templatetag = register.tag(templatetag)

class ExecNode(Node):
    def __init__(self,stmt):
        self.stmt = stmt

    def render(self,context):
        exec self.stmt in context
        return ''

def parse_exec(parser,token):
    cmd,stmt = token.contents.split(' ',1)
    return ExecNode(stmt)
parse_exec = register.tag('exec', parse_exec)



class IncludeNode(Node):
    def __init__(self,expr):
        self.expr = expr

    def render(self,context):
        name = eval(self.expr,context)
        template = open(name,'r').read()
        t = Template(template)
        return t.render(context)

def parse_include(parser,token):
    cmd,filename = token.contents.split(' ',1)
    return IncludeNode(filename)
parse_include = register.tag('include', parse_include)

class IfNode(Node):
    """ Removed the whole link stuff
    """
    def __init__(self,expr,nodelist_true,nodelist_false):
        self.expr = expr
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def render(self,context):
        value = eval(self.expr,context)
        if value:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

def parse_if(parser,token):
    """ Removed bit stuff and replaced it with the expression
    which is eval()'d
    """
    command, condition = token.contents.split(' ',1)
    if not condition:
        raise TemplateSyntaxError("'if' statement requires a condition statement")
    nodelist_true = parser.parse(('else', 'endif'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endif',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return IfNode(condition, nodelist_true, nodelist_false)
parse_if = register.tag('if', parse_if)

class ForNode(Node):
    def __init__(self,loop_var,iterable,body):
        self.loop_var = loop_var 
        self.iterable = iterable
        self.body = body

    def render(self,context):
        s = ''
        for n in eval(self.iterable,context):
            context[self.loop_var] = n
            s += self.body.render(context)
        return s


def do_for(parser, token):
    """ Did not work, so rewritten
    """
    cmd, loop_var, kw_in, iterable = token.contents.split(' ',3)
    if kw_in != 'in':
        SyntaxError("The for command hast the format for <loop_var> in <iterable>") 
    body = parser.parse(('endfor',))
    parser.next_token()
    return ForNode(loop_var,iterable,body)
do_for = register.tag("for", do_for)





