from actuator.package import REGISTRY
from actuator.components import decorators
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
        'fn_source': lambda cls: inspect.getsource(decorators.undecorate(cls)),
        'parse': lambda n: makeparse(path, package).parse(n),
        'signature': Signature,
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
        
        #Get the docstring for the component
        docstring = inspect.getdoc(decorators.undecorate(o))
        if docstring: docstring = inspect.cleandoc(docstring)
        if not docstring: return ""
        
        #Parse the input into the document
        parser.parse(docstring, document)
        
        doc_body = self.render(document)
        doc_fields = Signature(o).render()
        
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
            "#text": default,
        }

        #print((doc.tagname in tags, doc.tagname, doc))

        if not doc.tagname in tags:
            return default(doc)
        else:
            fn = tags[doc.tagname]
            return fn(doc)




class Signature:
    def __init__(self, cls):
        self._cls = decorators.undecorate(cls)

    @property
    def isempty(self):
        if len(self.params) > 0: return False
        if len(self.args) > 0: return False
        if self.input != None: return False
        if self.output != None: return False
        return True

    @property
    def _hooks(self): return decorators.lookup(self._cls)

    @property
    def args(self):
        return [h for h in self._hooks if isinstance(h, decorators.ArgumentHook)]
    
    @property
    def params(self):
        return [h for h in self._hooks if isinstance(h, decorators.ParameterHook)]
    
    @property
    def input(self):
        found = [h for h in self._hooks if isinstance(h, decorators.InputDescription)]
        return found[0] if found else None
    
    @property
    def output(self):
        found = [h for h in self._hooks if isinstance(h, decorators.OutputDescription)]
        return found[0] if found else None

    def render(self):
        if self.isempty: return ""
        
        source = '{}/templates/signature.html'.format(TEMPLATE_DIR)
        with open(source, 'r') as fh: contents = fh.read()
        return template(contents, {
            'signature': self,
        })


