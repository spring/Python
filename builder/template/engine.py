import re, sys
from inspect import getargspec

from template.context import Context, RequestContext, ContextPopException
from helper import *

__all__ = ('Template', 'Context', 'RequestContext', 'compile_string')

TOKEN_TEXT = 0
TOKEN_VAR = 1
TOKEN_BLOCK = 2
TOKEN_COMMENT = 3

# template syntax constants
FILTER_SEPARATOR = '|'
FILTER_ARGUMENT_SEPARATOR = ':'
VARIABLE_ATTRIBUTE_SEPARATOR = '.'
BLOCK_TAG_START = '{%'
BLOCK_TAG_END = '%}'
VARIABLE_TAG_START = '{{'
VARIABLE_TAG_END = '}}'
COMMENT_TAG_START = '{#'
COMMENT_TAG_END = '#}'
SINGLE_BRACE_START = '{'
SINGLE_BRACE_END = '}'

ALLOWED_VARIABLE_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.'

# what to report as the origin for templates that come from non-loader sources
# (e.g. strings)
UNKNOWN_SOURCE="&lt;unknown source&gt;"

# match a variable or block tag and capture the entire tag, including start/end delimiters
tag_re = re.compile('(%s.*?%s|%s.*?%s|%s.*?%s)' % (re.escape(BLOCK_TAG_START), re.escape(BLOCK_TAG_END),
                                          re.escape(VARIABLE_TAG_START), re.escape(VARIABLE_TAG_END),
                                          re.escape(COMMENT_TAG_START), re.escape(COMMENT_TAG_END)))

# global dictionary of libraries that have been loaded using get_library
libraries = {}
# global list of libraries to load by default for a new parser
builtins = []

# True if TEMPLATE_STRING_IF_INVALID contains a format string (%s). None means
# uninitialised.
invalid_var_format_string = None

class TemplateSyntaxError(Exception):
    def __str__(self):
        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO
        output = StringIO.StringIO()
        output.write(Exception.__str__(self))
        # Check if we wrapped an exception and print that too.
        if hasattr(self, 'exc_info'):
            import traceback
            output.write('\n\nOriginal ')
            e = self.exc_info
            traceback.print_exception(e[0], e[1], e[2], 500, output)
        return output.getvalue()

class TemplateDoesNotExist(Exception):
    pass

class TemplateEncodingError(Exception):
    pass

class VariableDoesNotExist(Exception):

    def __init__(self, msg, params=()):
        self.msg = msg
        self.params = params

    def __str__(self):
        return unicode(self).encode('utf-8')

class InvalidTemplateLibrary(Exception):
    pass

class Origin(object):
    def __init__(self, name):
        self.name = name

    def reload(self):
        raise NotImplementedError

    def __str__(self):
        return self.name

class StringOrigin(Origin):
    def __init__(self, source):
        super(StringOrigin, self).__init__(UNKNOWN_SOURCE)
        self.source = source

    def reload(self):
        return self.source

class Template(object):
    def __init__(self, template_string, origin=None, name='<Unknown Template>'):
        self.nodelist = compile_string(template_string, origin)
        self.name = name

    def __iter__(self):
        for node in self.nodelist:
            for subnode in node:
                yield subnode

    def render(self, context):
        "Display stage -- can be called many times"
        return self.nodelist.render(context)

def compile_string(template_string, origin):
    "Compiles template_string into NodeList ready for rendering"
    lexer_class, parser_class = Lexer, Parser
    lexer = lexer_class(template_string, origin)
    parser = parser_class(lexer.tokenize())
    return parser.parse()

class Token(object):
    def __init__(self, token_type, contents):
        # token_type must be TOKEN_TEXT, TOKEN_VAR, TOKEN_BLOCK or TOKEN_COMMENT.
        self.token_type, self.contents = token_type, contents

    def __str__(self):
        return '<%s token: "%s...">' % \
            ({TOKEN_TEXT: 'Text', TOKEN_VAR: 'Var', TOKEN_BLOCK: 'Block', TOKEN_COMMENT: 'Comment'}[self.token_type],
            self.contents[:20].replace('\n', ''))

    def split_contents(self):
        split = []
        bits = iter(smart_split(self.contents))
        for bit in bits:
            # Handle translation-marked template pieces
            if bit.startswith('_("') or bit.startswith("_('"):
                sentinal = bit[2] + ')'
                trans_bit = [bit]
                while not bit.endswith(sentinal):
                    bit = bits.next()
                    trans_bit.append(bit)
                bit = ' '.join(trans_bit)
            split.append(bit)
        return split

class Lexer(object):
    def __init__(self, template_string, origin):
        self.template_string = template_string
        self.origin = origin

    def tokenize(self):
        "Return a list of tokens from a given template_string."
        in_tag = False
        result = []
        for bit in tag_re.split(self.template_string):
            if bit:
                result.append(self.create_token(bit, in_tag))
            in_tag = not in_tag
        return result

    def create_token(self, token_string, in_tag):
        """
        Convert the given token string into a new Token object and return it.
        If in_tag is True, we are processing something that matched a tag,
        otherwise it should be treated as a literal string.
        """
        if in_tag:
            if token_string.startswith(VARIABLE_TAG_START):
                token = Token(TOKEN_VAR, token_string[len(VARIABLE_TAG_START):-len(VARIABLE_TAG_END)].strip())
            elif token_string.startswith(BLOCK_TAG_START):
                token = Token(TOKEN_BLOCK, token_string[len(BLOCK_TAG_START):-len(BLOCK_TAG_END)].strip())
            elif token_string.startswith(COMMENT_TAG_START):
                token = Token(TOKEN_COMMENT, '')
        else:
            token = Token(TOKEN_TEXT, token_string)
        return token

class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.tags = {}
        self.filters = {}
        for lib in builtins:
            self.add_library(lib)

    def parse(self, parse_until=None):
        if parse_until is None: parse_until = []
        nodelist = self.create_nodelist()
        while self.tokens:
            token = self.next_token()
            if token.token_type == TOKEN_TEXT:
                self.extend_nodelist(nodelist, TextNode(token.contents), token)
            elif token.token_type == TOKEN_VAR:
                if not token.contents:
                    self.empty_variable(token)
                var_node = self.create_variable_node(token.contents)
                self.extend_nodelist(nodelist, var_node,token)
            elif token.token_type == TOKEN_BLOCK:
                if token.contents in parse_until:
                    # put token back on token list so calling code knows why it terminated
                    self.prepend_token(token)
                    return nodelist
                try:
                    command = token.contents.split()[0]
                except IndexError:
                    self.empty_block_tag(token)
                # execute callback function for this tag and append resulting node
                self.enter_command(command, token)
                try:
                    compile_func = self.tags[command]
                except KeyError:
                    self.invalid_block_tag(token, command)
                try:
                    compiled_result = compile_func(self, token)
                except TemplateSyntaxError, e:
                    if not self.compile_function_error(token, e):
                        raise
                self.extend_nodelist(nodelist, compiled_result, token)
                self.exit_command()
        if parse_until:
            self.unclosed_block_tag(parse_until)
        return nodelist

    def skip_past(self, endtag):
        while self.tokens:
            token = self.next_token()
            if token.token_type == TOKEN_BLOCK and token.contents == endtag:
                return
        self.unclosed_block_tag([endtag])

    def create_variable_node(self, content):
        return VariableNode(content)

    def create_nodelist(self):
        return NodeList()

    def extend_nodelist(self, nodelist, node, token):
        if node.must_be_first and nodelist:
            try:
                if nodelist.contains_nontext:
                    raise AttributeError
            except AttributeError:
                raise TemplateSyntaxError("%r must be the first tag in the template." % node)
        if isinstance(nodelist, NodeList) and not isinstance(node, TextNode):
            nodelist.contains_nontext = True
        nodelist.append(node)

    def enter_command(self, command, token):
        pass

    def exit_command(self):
        pass

    def error(self, token, msg):
        return TemplateSyntaxError(msg)

    def empty_variable(self, token):
        raise self.error(token, "Empty variable tag")

    def empty_block_tag(self, token):
        raise self.error(token, "Empty block tag")

    def invalid_block_tag(self, token, command):
        raise self.error(token, "Invalid block tag: '%s'" % command)

    def unclosed_block_tag(self, parse_until):
        raise self.error(None, "Unclosed tags: %s " %  ', '.join(parse_until))

    def compile_function_error(self, token, e):
        pass

    def next_token(self):
        return self.tokens.pop(0)

    def prepend_token(self, token):
        self.tokens.insert(0, token)

    def delete_first_token(self):
        del self.tokens[0]

    def add_library(self, lib):
        self.tags.update(lib.tags)
        self.filters.update(lib.filters)

    def find_filter(self, filter_name):
        if filter_name in self.filters:
            return self.filters[filter_name]
        else:
            raise TemplateSyntaxError("Invalid filter: '%s'" % filter_name)

class TokenParser(object):
    """
    Subclass this and implement the top() method to parse a template line. When
    instantiating the parser, pass in the line from the Django template parser.

    The parser's "tagname" instance-variable stores the name of the tag that
    the filter was called with.
    """
    def __init__(self, subject):
        self.subject = subject
        self.pointer = 0
        self.backout = []
        self.tagname = self.tag()

    def top(self):
        "Overload this method to do the actual parsing and return the result."
        raise NotImplementedError()

    def more(self):
        "Returns True if there is more stuff in the tag."
        return self.pointer < len(self.subject)

    def back(self):
        "Undoes the last microparser. Use this for lookahead and backtracking."
        if not len(self.backout):
            raise TemplateSyntaxError("back called without some previous parsing")
        self.pointer = self.backout.pop()

    def tag(self):
        "A microparser that just returns the next tag from the line."
        subject = self.subject
        i = self.pointer
        if i >= len(subject):
            raise TemplateSyntaxError("expected another tag, found end of string: %s" % subject)
        p = i
        while i < len(subject) and subject[i] not in (' ', '\t'):
            i += 1
        s = subject[p:i]
        while i < len(subject) and subject[i] in (' ', '\t'):
            i += 1
        self.backout.append(self.pointer)
        self.pointer = i
        return s

    def value(self):
        "A microparser that parses for a value: some string constant or variable name."
        subject = self.subject
        i = self.pointer
        if i >= len(subject):
            raise TemplateSyntaxError("Searching for value. Expected another value but found end of string: %s" % subject)
        if subject[i] in ('"', "'"):
            p = i
            i += 1
            while i < len(subject) and subject[i] != subject[p]:
                i += 1
            if i >= len(subject):
                raise TemplateSyntaxError("Searching for value. Unexpected end of string in column %d: %s" % (i, subject))
            i += 1
            res = subject[p:i]
            while i < len(subject) and subject[i] in (' ', '\t'):
                i += 1
            self.backout.append(self.pointer)
            self.pointer = i
            return res
        else:
            p = i
            while i < len(subject) and subject[i] not in (' ', '\t'):
                if subject[i] in ('"', "'"):
                    c = subject[i]
                    i += 1
                    while i < len(subject) and subject[i] != c:
                        i += 1
                    if i >= len(subject):
                        raise TemplateSyntaxError("Searching for value. Unexpected end of string in column %d: %s" % (i, subject))
                i += 1
            s = subject[p:i]
            while i < len(subject) and subject[i] in (' ', '\t'):
                i += 1
            self.backout.append(self.pointer)
            self.pointer = i
            return s

class Node(object):
    # Set this to True for nodes that must be first in the template (although
    # they can be preceded by text nodes.
    must_be_first = False

    def render(self, context):
        "Return the node rendered as a string"
        pass

    def __iter__(self):
        yield self

    def get_nodes_by_type(self, nodetype):
        "Return a list of all nodes (within this node and its nodelist) of the given type"
        nodes = []
        if isinstance(self, nodetype):
            nodes.append(self)
        if hasattr(self, 'nodelist'):
            nodes.extend(self.nodelist.get_nodes_by_type(nodetype))
        return nodes

class NodeList(list):
    # Set to True the first time a non-TextNode is inserted by
    # extend_nodelist().
    contains_nontext = False

    def render(self, context):
        bits = []
        for node in self:
            if isinstance(node, Node):
                bits.append(self.render_node(node, context))
            else:
                bits.append(node)
        return str(''.join([str(b) for b in bits]))

    def get_nodes_by_type(self, nodetype):
        "Return a list of all nodes of the given type"
        nodes = []
        for node in self:
            nodes.extend(node.get_nodes_by_type(nodetype))
        return nodes

    def render_node(self, node, context):
        return node.render(context)

class TextNode(Node):
    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return "<Text Node: '%s'>" % str(self.s[:25], 'ascii',
                errors='replace')

    def render(self, context):
        return self.s
    
def _render_value_in_context(value, context):
    """
    Converts any value to a string to become part of a rendered template. This
    means escaping, if required, and conversion to a unicode object. If value
    is a string, it is expected to have already been translated.
    """
    return str(value)

class VariableNode(Node):
    def __init__(self,expr):
        self.expr = expr

    def render(self,context):
        return str(eval(self.expr,context))

def generic_tag_compiler(params, defaults, name, node_class, parser, token):
    "Returns a template.Node subclass."
    bits = token.split_contents()[1:]
    bmax = len(params)
    def_len = defaults and len(defaults) or 0
    bmin = bmax - def_len
    if(len(bits) < bmin or len(bits) > bmax):
        if bmin == bmax:
            message = "%s takes %s arguments" % (name, bmin)
        else:
            message = "%s takes between %s and %s arguments" % (name, bmin, bmax)
        raise TemplateSyntaxError(message)
    return node_class(bits)

class Library(object):
    def __init__(self):
        self.filters = {}
        self.tags = {}

    def tag(self, name=None, compile_function=None):
        if name == None and compile_function == None:
            # @register.tag()
            return self.tag_function
        elif name != None and compile_function == None:
            if(callable(name)):
                # @register.tag
                return self.tag_function(name)
            else:
                # @register.tag('somename') or @register.tag(name='somename')
                def dec(func):
                    return self.tag(name, func)
                return dec
        elif name != None and compile_function != None:
            # register.tag('somename', somefunc)
            self.tags[name] = compile_function
            return compile_function
        else:
            raise InvalidTemplateLibrary("Unsupported arguments to Library.tag: (%r, %r)", (name, compile_function))

    def tag_function(self,func):
        self.tags[getattr(func, "_decorated_function", func).__name__] = func
        return func

    def filter(self, name=None, filter_func=None):
        if name == None and filter_func == None:
            # @register.filter()
            return self.filter_function
        elif filter_func == None:
            if(callable(name)):
                # @register.filter
                return self.filter_function(name)
            else:
                # @register.filter('somename') or @register.filter(name='somename')
                def dec(func):
                    return self.filter(name, func)
                return dec
        elif name != None and filter_func != None:
            # register.filter('somename', somefunc)
            self.filters[name] = filter_func
            return filter_func
        else:
            raise InvalidTemplateLibrary("Unsupported arguments to Library.filter: (%r, %r)", (name, filter_func))

    def filter_function(self, func):
        self.filters[getattr(func, "_decorated_function", func).__name__] = func
        return func

    def simple_tag(self,func):
        params, xx, xxx, defaults = getargspec(func)

        class SimpleNode(Node):
            def __init__(self, vars_to_resolve):
                self.vars_to_resolve = map(Variable, vars_to_resolve)

            def render(self, context):
                resolved_vars = [var.resolve(context) for var in self.vars_to_resolve]
                return func(*resolved_vars)

        compile_func = curry(generic_tag_compiler, params, defaults, getattr(func, "_decorated_function", func).__name__, SimpleNode)
        compile_func.__doc__ = func.__doc__
        self.tag(getattr(func, "_decorated_function", func).__name__, compile_func)
        return func

    def inclusion_tag(self, file_name, context_class=Context, takes_context=False):
        def dec(func):
            params, xx, xxx, defaults = getargspec(func)
            if takes_context:
                if params[0] == 'context':
                    params = params[1:]
                else:
                    raise TemplateSyntaxError("Any tag function decorated with takes_context=True must have a first argument of 'context'")

            class InclusionNode(Node):
                def __init__(self, vars_to_resolve):
                    self.vars_to_resolve = map(Variable, vars_to_resolve)

                def render(self, context):
                    resolved_vars = [var.resolve(context) for var in self.vars_to_resolve]
                    if takes_context:
                        args = [context] + resolved_vars
                    else:
                        args = resolved_vars

                    dict = func(*args)

                    if not getattr(self, 'nodelist', False):
                        from template.loader import get_template, select_template
                        if not isinstance(file_name, basestring) and is_iterable(file_name):
                            t = select_template(file_name)
                        else:
                            t = get_template(file_name)
                        self.nodelist = t.nodelist
                    return self.nodelist.render(context_class(dict,
                            autoescape=context.autoescape))

            compile_func = curry(generic_tag_compiler, params, defaults, getattr(func, "_decorated_function", func).__name__, InclusionNode)
            compile_func.__doc__ = func.__doc__
            self.tag(getattr(func, "_decorated_function", func).__name__, compile_func)
            return func
        return dec

def get_library(module_name):
    lib = libraries.get(module_name, None)
    if not lib:
        try:
            mod = import_module(module_name)
        except ImportError, e:
            raise InvalidTemplateLibrary("Could not load template library from %s, %s" % (module_name, e))
        try:
            lib = mod.register
            libraries[module_name] = lib
        except AttributeError:
            raise InvalidTemplateLibrary("Template library %s does not have a variable named 'register'" % module_name)
    return lib

def add_to_builtins(module_name):
    builtins.append(get_library(module_name))

add_to_builtins('template.defaulttags')
