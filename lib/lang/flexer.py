
#A Flexible LEXER based off of shlex with a queue-style API
class Flexer(object):
    def __init__(self, given):
        import shlex
        if isinstance(given, str):
            import shlex
            lex = shlex.shlex(given, posix=False)
        elif isinstance(given, shlex.shlex):
            lex = given
        else:
            raise Exception("Argument 'given' is of unknown type")
        self._lex = lex

    @property
    def lexer(self): return self._lex

    def push(self, token):
        self.lexer.push_token(token)

    def pop(self, *expected):
        token = self.lexer.get_token()
        if not expected: return token
        if token in expected: return token

        #not expected, raise an exception
        if len(expected) > 1:
            raise Exception("Unexpected token '%s'. Expeced one of %s" % (token, expected))
        else:
            raise Exception("Unexpected token '%s'. Expected '%s'" % (token, expected))
    
    def pop_if(self, *expected):
        token = self.peek()
        if token in expected: self.pop()
        return token

    def peek(self, *expected):
        token = self.pop(*expected)
        self.push(token)
        return token

    def all_tokens(self):
        tokens = []
        while self.peek():
            tokens += [self.pop()]
        replace = tokens[:]
        while replace:
            self.push(replace[-1])
            replace = replace[:-1]
        return tokens

class ParserHook(object):
    def __init__(self, name, test, callback):
        self.name = name
        self.test = test
        self.callback = callback

class FlexParser(object):
    def __init__(self, given, use_symbols=True):
        if isinstance(given, str):
            self._flexer = Flexer(given)
        elif isinstance(given, Flexer):
            self._flexer = given
        else:
            raise Exception("Argument 'given' is of unknown type")

        self._value_hooks = {}
        self._token_hooks = {}

        self._use_symbols = use_symbols

        #Run mixin init methods if this is the first superclass 
        #and there are others after it
        supers = self.__class__.mro()
        if supers[1] == FlexParser:
            supers = supers[2:]
            while True:
                if supers[0] == object: break
                supers[0].__init__(self)
                supers = supers[1:]


    @property
    def flexer(self): return self._flexer

    #delegates
    def pop(self, *args, **kwargs): return self.flexer.pop(*args, **kwargs)
    def pop_if(self, *args, **kwargs): return self.flexer.pop_if(*args, **kwargs)
    def peek(self, *args, **kwargs): return self.flexer.peek(*args, **kwargs)
    def push(self, *args, **kwargs): return self.flexer.push(*args, **kwargs)

    def _add_value_hook(self, name, test, callback):
        hook = ParserHook(name, test, callback)
        if hook.name in self._value_hooks: raise Exception("value hook with name '%s' already registered" % hook.name)
        self._value_hooks[hook.name] = hook

    def _add_token_hook(self, name, test, callback):
        hook = ParserHook(name, test, callback)
        if hook.name in self._token_hooks: raise Exception("token hook with name '%s' already registered" % hook.name)
        self._token_hooks[hook.name] = hook

    #parse all input
    def parse(self):
        results = []
        while self.peek():
            results.append(self.parse_token())
        return results
            

    #Parses the next token from the lexer in a generic way and returns... something
    def can_parse_token(self):
        token = self.peek()
        #go through all hooks and see if any of them match
        for hook in self._token_hooks.values():
            if hook.test(token):
                return False

    def parse_token(self):
        token = self.peek()
        #go through all hooks and see if any of them match
        for hook in self._token_hooks.values():
            if hook.test(token):
                return hook.callback()

        raise Exception("Could not interpret token '%s'" % token)
        

    #Parses the next value (value as in eg: key=value pair) from the lexer
    def parse_value(self):
        value = self.peek()

        #go through all hooks and see if any of them match
        for hook in self._value_hooks.values():
            if hook.test(value):
                return hook.callback()

        #Just parse it as a single value
        self.pop()
        if self._use_symbols:
            return Symbol(value)
        else:
            return value



#A Sequence PARSER for reading values or sequences of values
class SequenceParserMixin(object):
    def __init__(self):
        pass
        #self._add_value_hook("seq.list", lambda t: t == "[", lambda: self.parse_list())
        #self._add_value_hook("seq.dict", lambda t: t == "{", lambda: self.parse_dict())
        #this is not a value in the sense that you would just encounter it in 
        #place of, say, an integer. It is used in specific locations like function invocations
        #we want to retain the ability to parse it without having it be parsed automatically
        #anywhere it pops up
        #self._add_value_hook("seq.keyvalue", lambda t: t == "(", lambda: self.parse_keyvalue())


    #Parses a sequence of comma-separated entries, calling on_entry 
    #each time it reads the first token of a new entry
    def parse_sequence(self, initiator, terminator, on_entry):
        last = None
        self.flexer.pop(initiator)
        while True:
            value = self.flexer.pop_if(",", terminator)
            if value == terminator: 
                return
            elif value == "":
                raise Exception("Unexpected end of input")
            elif value == ",": 
                if last == None: raise Exception("Commas must come after values")
                if last == ",": raise Exception("Commas must separate values")
                continue
            else:
                last = value
                on_entry()

    #Parses (key=value, ...) items.
    def parse_keyvalue(self):
        items = {}
        def on_entry():
            key = self.flexer.pop()
            t = self.flexer.pop_if("=")
            value = self.parse_value() if t == "=" else True 
            if key in items: raise Exception("Parameter '%s' already specified" % key)
            items[key] = value
        self.parse_sequence("(", ")", on_entry)
        return items

    #Parses (value, key=value, ...) items.
    def parse_args(self):
        args = []
        kwargs = {}
        def on_entry():
            first = self.parse_value()
            kvmode = self.flexer.pop_if("=") == "="
            if kvmode:
                key = first
                if isinstance(key, Symbol): key = key.name
                if not isinstance(key, str): raise Exception("Key must be a string")
                value = self.parse_value()
                if key in kwargs: raise Exception("Parameter '%s' already specified" % key)
                kwargs[key] = value
            else:
                args.append(first)

        self.parse_sequence("(", ")", on_entry)
        return (args, kwargs)

    #Parses a list of items.
    def parse_list(self):
        items = []
        self.parse_sequence("[", "]", lambda: items.append(self.parse_value()))
        return items

    #parses a dictionary/map of items.
    def parse_dict(self):
        items = {}
        def on_entry():
            key = self.parse_value()
            if not isinstance(key, str): raise Exception("Key must be a string")
            if key in items: raise Exception("Key '%s' already defined" % key) 
            self.flexer.pop(":")
            value = self.parse_value()
            items[key] = value
        self.parse_sequence("{", "}", on_entry)
        return items






#value hooks for primitive data types
class PrimitivesParserMixin(object):
    def __init__(self):
        self._add_value_hook(
            "primitive.string",
            lambda t: t[0] in self.flexer.lexer.quotes and t[-1] in self.flexer.lexer.quotes,
            lambda: self.pop()[1:-1]
        )
        self._add_value_hook(
            "primitive.int",
            lambda t: self.is_int(t),
            lambda: int(self.pop())
        )
        self._add_value_hook(
            "primitive.float",
            lambda t: self.is_float(t),
            lambda: float(self.pop())
        )
        self._add_value_hook(
            "primitive.boolean",
            lambda t: self.is_bool(t),
            lambda: self.parse_bool(self.pop())
        )


    def is_int(self, s):
        try:
            int(s)
            return True
        except:
            return False

    def is_float(self, s):
        try:
            float(s)
            return True
        except:
            return False

    def is_bool(self, s):
        return s in ['True', 'False']

    def parse_bool(self, s):
        return s == 'True'


class Symbol(object):
    def __init__(self, name):
        self._name = name

    @property
    def name(self): return self._name

    def __repr__(self): return "<Symbol '%s'>" % self.name

    def __eq__(self, other):
        if not isinstance(other, Symbol): return False 
        return self.name == other.name

class BlockParserMixin(object):
    def __init__(self):
        self._add_token_hook(
            "block.parse", 
            lambda t: t == "{", 
            lambda: self.parse_block()
        )

    def parse_block(self):
        self.pop("{")
        elements = []
        while True:
            if self.pop_if("}") == "}": break
            elements += [self.parse_token()]
        return elements


class SExpression(object):
    def __init__(self, items):
        self._items = items

    @property
    def items(self): return self._items

    def __repr__(self): return "<S-Expression %s>" % self.items

class SExpressionMixin(object):
    def __init__(self):
        self._add_token_hook(
            "sexp.expression",
            lambda t: t == "(",
            lambda: self.parse_sexpression()
        )
    
    def parse_sexpression(self):
        self.pop("(")
        items = []
        while True:
            if self.peek() == ")":
                self.pop() 
                break
            if self.can_parse_token():
                items.append(self.parse_token())
            else:
                items.append(self.parse_value())
        return SExpression(items)



