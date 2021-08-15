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
        'source': Source,
        'signature': Signature,
        'documentation': Documentation,
    }
    template_file(
        '{}/templates/package.html'.format(TEMPLATE_DIR),
        '{}/pkg-{}.html'.format(path, package.name),
        values
    )

class Source:
    def __init__(self, cls):
        self._cls = decorators.undecorate(cls)

    @property
    def source(self):
        source = inspect.getsource(self._cls)
        
        #trim leading/tailing blank lines
        lines = source.split("\n")
        while lines:
            if lines[0].strip() == "": 
                lines = lines[1:]
            else:
                break
        while lines:
            if lines[-1].strip() == "": 
                lines = lines[:-1]
            else:
                break
        source = "\n".join(lines)
        
        return source

    def render(self):       
        from pygments import highlight
        from pygments.lexers import PythonLexer
        from pygments.formatters import HtmlFormatter
        html = highlight(self.source, PythonLexer(), HtmlFormatter())
        
        return html

class Documentation:
    def __init__(self, cls):
        self._cls = decorators.undecorate(cls)
    
    @property
    def docstring(self):
        #Get the docstring for the component
        docstring = inspect.getdoc(decorators.undecorate(self._cls))
        if docstring: docstring = inspect.cleandoc(docstring)
        if not docstring: docstring = ""
        return docstring
    
    def render(self):
        #Thanks: https://stackoverflow.com/questions/32167384/how-do-i-convert-a-docutils-document-tree-into-an-html-string
        from docutils.core import publish_doctree, publish_from_doctree
        #parse the docstring
        tree = publish_doctree(self.docstring)
        
        #convert it to html
        html = publish_from_doctree(tree, writer_name='html').decode()
        
        return html

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


