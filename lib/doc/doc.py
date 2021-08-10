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
        
    colours = {
        'header_colour': '#faf0e1',
        'header_border_colour': '#6b5b3b',
        'theme_colour': '#006f5c',
        'sidebar_colour': '#fff',
        'sidebar_border': '#fff',
        'body_colour': '#fff',
        'link_colour': '#006f5c',
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
    }
    template_file(
        '{}/templates/package.html'.format(TEMPLATE_DIR),
        '{}/pkg-{}.html'.format(path, package.name),
        values
    )

    
