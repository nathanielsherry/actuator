from actuator.components.source import Source

from actuator.components.decorators import parameter, argument, input, output, allarguments, source

@output('bool', 'Boolean True')
@source
def true():
    """    
    Outputs a boolean True value
    """
    return True


@output('bool', 'Boolean False')
@source
def false():
    """    
    Outputs a boolean False value
    """
    return False
