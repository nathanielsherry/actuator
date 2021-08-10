from actuator.package import REGISTRY
import jinja2
import os, shutil

TEMPLATE_DIR = os.path.dirname(__file__)

def template_file(source, dest, values):
    with open(source, 'r') as fh: contents = fh.read()
    result = jinja2.Template(contents).render(values)
    with open(dest, 'w') as fh: fh.write(result)

def create(path):
    try:
        os.makedirs(path)
    except: 
        pass
    
    for package in REGISTRY.packages:
        template_package(path, package)

    orange = {
        'header_colour': '#333',
        'header_shadow_colour': '#aaa',
        'theme_colour': '#fb8c00',
        'sidebar_colour': '#eee',
        'sidebar_border': '#bbb',
        'body_colour': '#fff',
    }
        
    purple = {
        'header_colour': '#fff',
        'header_shadow_colour': '#aaa',
        'theme_colour': '#461A99',
        'sidebar_colour': '#eee',
        'sidebar_border': '#bbb',
        'body_colour': '#fff',
    }
        
    template_file(        
        '{}/templates/style.css'.format(TEMPLATE_DIR),
        '{}/style.css'.format(path),
        purple
    )

def template_package(path, package):
    values = {
        'pkg': package,
        'pkgs': REGISTRY.packages,
    }
    template_file(
        '{}/templates/package.html'.format(TEMPLATE_DIR),
        '{}/pkg-{}.html'.format(path, package.name),
        values
    )

    
