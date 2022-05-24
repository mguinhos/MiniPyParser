# examples/main.py

from minipyparser import tokenizer
from minipyparser import parser

for ast in parser.parse(tokenizer.tokenize(open("hello_world.py"))):
    print(ast)