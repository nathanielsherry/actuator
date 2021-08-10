from actuator.package import REGISTRY
import jinja2
import os, shutil

TEMPLATE_DIR = os.path.dirname(__file__)

def create(path):
    try:
        os.makedirs(path)
    except: 
        pass
    
    for package in REGISTRY.packages:
        create_package(path, package)
    shutil.copy('{}/templates/style.css'.format(TEMPLATE_DIR), '{}/style.css'.format(path))

def create_package(path, package):
    contents = render_package(package, {})
    with open('{}/pkg-{}.html'.format(path, package.name), 'w') as fh: fh.write(contents)

def render_package(package, values):
    
    with open('{}/templates/package.html'.format(TEMPLATE_DIR), 'r') as fh: contents = fh.read()

    values = {
        'pkg': package,
        'pkgs': REGISTRY.packages,
    }
    
    return jinja2.Template(contents).render(values)

def render_item(package, item, values):
    name = cls.__name__
    doc = cls.__doc__
    mod = cls.__module__
    
    
