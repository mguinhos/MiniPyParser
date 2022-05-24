# MiniPyParser
A minimal python parser, written in python

[![Upload Python Package](https://github.com/mguinhos/MiniPyParser/actions/workflows/python-publish.yml/badge.svg)](https://github.com/mguinhos/MiniPyParser/actions/workflows/python-publish.yml)

[View License](./LICENSE.md)

## Installing
### Local
```
$ pip install -e minipyparser
```
### PyPI
```
$ pip install minipyparser
```


## Using
```python
# examples/hello_world.py

print("hello, from mars!")
```
```python
# examples/main.py

from minipyparser import tokenizer
from minipyparser import parser

for ast in parser.parse(tokenizer.tokenize(open("hello_world.py"))):
    print(ast)
```
```
$ cd examples
$ python main.py

Comment(value='examples/hello_world.py')
Call(head=Name(print), args=[Literal(value='hello, from mars!')])
```

2022 - Marcel Guinhos