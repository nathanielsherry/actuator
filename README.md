# Actuator

Actuator attempts to go beyond the pipeline model of unix processes by using a source/sink model which allows features like polling and rich data manipulation.

## Expressions

Actuator expressions take the form:

    from <source> via <operator> to <sink> on <monitor>

### Source
A Source supplies some kind of input to the processing pipeline on demand. If no source is specified in an Actuator expression, the default is to read the entirety of stdin.

### Operator
An Operator performs intermediate transformations on the input provided by a Source. The kind of operations used depends on the kind of data being introduced into the pipeline. No operators are required, however, as a source is a special type of operator, and the expression is valid without them.

Operators may be chained together with the pipe symbol in order to compose them in the same way you would compose shell commands. One key difference is that it is not text moving between operators, but rather an arbitrary data payload. This means that you don't need to worry about line breaks and how the next operator will parse the previous one's output. Just so long as the types match.

### Sink
A Sink accepts data at the end of the pipeline and performs some action with it. The action may be a side-effect such as writing to a file, it may expose information for retrieval, or it may do nothing at all (see `sh.null`).

### Monitor
The Monitor defines the repetition strategy for a pipeline. For example, with `on start`, a pipeline will fire only once, whereas with `on interval`, a pipeline will fire once per second. 

If no monitor is specified, the Sink is given the opportunity to provide one. This is useful for sinks like `sh.curses` which prefers an Interval monitor, or `net.serve` which prefers an OnDemand monitor so that it may run the pipeline whenever a GET request is received.

## Examples

Expose machine status in a YAML document via REST URL:

    act 'from `lscpu --json` via fmt.fromjson|fmt.toyaml to net.serve'

Note that without a monitor specified, the `net.serve` Sink will supply an OnDemand monitor. To prevent large numbers of GET requests from firing the pipeline too often, a `cached` operator may be added anywhere in the operator section.

Reproduce `watch` functionality:

    act 'from `tail -n10 /var/log/messages` to sh.curses'

As with the previous example, the Sink provides the Monitor, this time an Interval. No operators are specified in this example.

Poll a URL and watch for changes, printing 'True' when detected:

    act 'from net.url["http://www.example.com"] via change on interval(sleep=120)'
    
This example does not specify a Sink, so the default of writing to standard out is used.
    