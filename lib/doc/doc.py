from actuator.package import REGISTRY
from collections import OrderedDict
import jinja2
import os, shutil, inspect

TEMPLATE_DIR = os.path.dirname(__file__)

def template(contents, values):
    return jinja2.Template(contents).render(values)

def template_file(source, dest, values):
    with open(source, 'r') as fh: contents = fh.read()
    result = template(contents, values)
    with open(dest, 'w') as fh: fh.write(result)

def create(path):
    try:
        os.makedirs(path)
    except: 
        pass
    
    for package in REGISTRY.packages:
        template_package(path, package)
        
    colours = {
        'theme_colour': '#006f5c',
        'accent_colour': '#6b5b3b',
        'page_colour': '#faf0e1',
        'background_colour': '#fff',
        'transparent': 'argb(255, 255, 255, 0.0)',
    }
    
    template_file(        
        '{}/templates/style.css'.format(TEMPLATE_DIR),
        '{}/style.css'.format(path),
        colours
    )

def template_package(path, package):
    values = {
        'pkg': package,
        'pkgs': REGISTRY.packages,
        'fn_source': inspect.getsource,
        'parse': lambda n: makeparse(path, package).parse(n),
    }
    template_file(
        '{}/templates/package.html'.format(TEMPLATE_DIR),
        '{}/pkg-{}.html'.format(path, package.name),
        values
    )

def makeparse(path, package):
    return DocParser(path, package)

class DocParser:
    def __init__(self, path, package):
        self._path = path
        self._package = package
        self._fieldlist = FieldList()

    def parse(self, o):
        import docutils
        from docutils.parsers.rst import Parser
        from docutils.utils import new_document
        
        #Create the parser
        parser = Parser()
        
        #Create target document
        settings = docutils.frontend.OptionParser(
            components=(docutils.parsers.rst.Parser,)
            ).get_default_values()
        document = new_document('', settings)
        
        if not o.__doc__: return ""
        
        #Parse the input into the document
        parser.parse(o.__doc__, document)
        
        doc_body = self.render(document)
        doc_fields = self._fieldlist.render()
        
        return doc_fields + doc_body
        
    def render(self, doc):

        def default(n):

            if isinstance(n, str):
                return str(n)                
            if n.children:
                return "\n".join([self.render(c) for c in n.children])
            elif hasattr(n, 'rawsource'):
                return n.rawsource 
            else:
                return ""
        
        def tag(tag, nested=None, raw=False, classes=None):
            if not classes: classes = []
            def inner(n):
                source = None
                if nested:
                    source = nested(n)
                elif raw:
                    source = n.rawsource
                else:
                    source = default(n)
                    
                return "<{tag} class='{classes}'>{source}</{tag}>".format(
                    source=source,
                    classes=" ".join(classes),
                    tag=tag
                )
            
            return inner
        
        def titled(title, nested=None, kind=None):
            if not nested: nested = default
            if not kind: kind=title.lower()
            def inner(n):
                source = nested(n)
                return "<div class='component-doc-{kind}'><div class='component-doc-{kind}-title'>{title}</div><div class='component-doc-{kind}-body'>{source}</div></div>".format(
                    source=source,
                    kind=kind,
                    title=title,
                )
            return inner
                   
        
        def field(n):
            if not len(n.children) == 2: return default(n)
            node_name = n.children[0]
            node_body = n.children[1]
            decl = node_name.children[0].split(' ')
            desc = default(node_body)
            
            
            
            fieldtype = decl[0]
            fieldname = None
            if len(decl) >= 2: fieldname = decl[1]
            
            fieldtype = fieldtype.lower()
            
            #print((fieldtype, fieldname))
            
            if fieldtype == 'param':
                if not fieldname: return default(n)
                self._fieldlist.set_param_desc(fieldname, desc)
            elif fieldtype == 'type':
                if not fieldname: return default(n)
                self._fieldlist.set_param_type(fieldname, desc)
            
            elif fieldtype == 'output':
                self._fieldlist.set_outputvalue(desc)
            elif fieldtype == 'outtype':
                self._fieldlist.set_outputtype(desc)
            
            elif fieldtype == 'input':
                self._fieldlist.set_inputvalue(desc)
            elif fieldtype == 'intype':
                self._fieldlist.set_inputtype(desc)
            
            elif fieldtype == 'example':
                self._fieldlist.set_example(desc)
            
            else:
                return titled(node_name.children[0], tag('div'), kind='field')(node_body)
            
            return ""
            
        
        tags = {
            "paragraph": tag('p'),
            "block_quote": tag('span'),
            "bullet_list": tag('ul'),
            "list_item": tag('li'),
            "strong": tag('b'),
            "literal_block": tag('div', raw=True, classes=['component-doc-literalblock']),
            "problematic": tag('div', raw=True, classes=['component-doc-problematic']),
            "note": titled('Note'),
            "warning": titled('Warning'),
            "doctest_block": titled('Example', tag('div', raw=True, classes=['component-doc-literalblock'])),
            "field": field,
            "#text": default,
        }

        #print((doc.tagname in tags, doc.tagname, doc))

        if not doc.tagname in tags:
            return default(doc)
        else:
            fn = tags[doc.tagname]
            return fn(doc)

        
            
    

    

"""
Return a new empty document object.
:Parameters:
    `source_path` : string
        The path to or description of the source text of the document.
    `settings` : optparse.Values object
        Runtime settings.  If none are provided, a default core set will
        be used.  If you will use the document object with any Docutils
        components, you must provide their default settings as well.  For
        example, if parsing rST, at least provide the rst-parser settings,
        obtainable as follows::
            settings = docutils.frontend.OptionParser(
                components=(docutils.parsers.rst.Parser,)
                ).get_default_values()
"""

class FieldList:
    def __init__(self):
        self._params = OrderedDict()
        self._input_val=None
        self._input_type=None
        self._output_val=None
        self._output_type=None
        self._example = None

    @property
    def isempty(self):
        if len(self._params) > 0: return False
        if self.inputtype != None: return False
        if self.inputvalue != None: return False
        if self.outputtype != None: return False
        if self.outputvalue != None: return False
        if self.example != None: return False
        return True

    @property
    def inputtype(self): return self._input_type
    def set_inputtype(self, itype): self._input_type = itype
    
    @property
    def inputvalue(self): return self._input_val
    def set_inputvalue(self, ival): self._input_val = ival
    
    @property
    def outputtype(self): return self._output_type
    def set_outputtype(self, otype): self._output_type = otype
    
    @property
    def outputvalue(self): return self._output_val
    def set_outputvalue(self, oval): self._output_val = oval
    
    @property
    def example(self): return self._example
    def set_example(self, oval): self._example = oval
    
    def param(self, name):
        if name in self._params:
            return self._params[name]
        else:
            return None
    
    def set_param_type(self, name, ptype):
        if not self.param(name): self._params[name] = {}
        self.param(name)['type'] = ptype

    def set_param_desc(self, name, desc):
        if not self.param(name): self._params[name] = {}
        self.param(name)['desc'] = desc

    @property
    def params(self):
        return self._params

    def render(self):
        if self.isempty: return ""
        
        source = '{}/templates/signature.html'.format(TEMPLATE_DIR)
        with open(source, 'r') as fh: contents = fh.read()
        return template(contents, {
            'outval': self.outputvalue,
            'outtype': self.outputtype,
            'inval': self.inputvalue,
            'intype': self.inputtype,
            'params': self.params,
            'example': self.example,
        })
