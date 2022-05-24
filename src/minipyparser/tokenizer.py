from enum import Enum

from dataclasses import dataclass
from io import TextIOBase

from .hook import BaseHook, TextHook

class TokenHook(BaseHook):
    def take(self, count=1) -> "AnyToken":
        if count > 1:
            return tuple(self.take() for _ in range(count))

        if self.index < len(self.cache):
            cached = self.cache[self.index]
        else:
            try:
                cached = next(self.source)
            except StopIteration:
                cached = None
                
            self.cache.append(cached)

        self.index += 1
        
        return cached

class BaseToken:
    def __hash__(self):
        return hash(self.value)
    
    def __bool__(self):
        return True
    
    def __len__(self):
        return len(self.value)
    
    def __repr__(self):
        return str(self)
    
    def __eq__(self, value: str):
        return self.value == value
    
    @classmethod
    def scan(cls, hook: TextHook):
        raise NotImplementedError

class Token(BaseToken, Enum):
    LeftParenthesis=    '('
    RightParenthesis=   ')'
    LeftBrace=          '{'
    RightBrace=         '}'
    LeftBracket=        '['
    RightBracket=       ']'

    Arrow=              '->'

    Ellipsis=           '...'
    Colon=              ':'
    Semicolon=          ';'
    Dot=                '.'
    Comma=              ','

    Equal=              '='
    GreaterThan=        '>'
    LessThan=           '<'
    Plus=               '+'
    Minus=              '-'
    Star=               '*'
    StarStar=           '**'
    Slash=              '/'
    SlashSlash=         '//'
    Percent=            '%'
    And=                '&'
    Or=                 '|'
    Xor=                '^'
    Neg=                '~'
    LeftShift=          '<<'
    RightShift=         '>>'

    NotEqual=           '!='
    EqualEqual=         '=='
    GreaterThanEqual=   '>='
    LessThanEqual=      '<='
    PlusEqual=          '+='
    MinusEqual=         '-='
    StarEqual=          '*='
    StarStarEqual=      '**='
    SlashEqual=         '/='
    SlashSlashEqual=    '//='
    PercentEqual=       '%='
    AndEqual=           '&='
    OrEqual=            '|='
    XorEqual=           '^='
    NegEqual=           '~='
    LeftShiftEqual=     '<<='
    RightShiftEqual=    '>>='
    
    At=                 '@'

    @classmethod
    def scan(cls, hook: TextHook):
        hook.drop()

        for token in TOKENS:
            if hook.test(token.value):
                return token
        
        raise ValueError(f"invalid token '{hook.take()}'")

TOKENS = sorted(Token, key=len, reverse=True)
BINARY_OPERATORS = {Token.Plus, Token.Minus, Token.Star, Token.StarStar, Token.Slash, Token.SlashSlash, Token.Percent, Token.And, Token.Or, Token.Xor, Token.LeftShift, Token.RightShift, Token.GreaterThan, Token.LessThan, Token.NotEqual, Token.EqualEqual, Token.GreaterThanEqual, Token.LessThanEqual}
UNARY_OPERATORS = {Token.Plus, Token.Minus, Token.Neg}

class Keyword(BaseToken, Enum):
    Pass=               'pass'
    Import=             'import'
    From=               'from'
    As=                 'as'
    Class=              'class'
    Def=                'def'
    Return=             'return'
    Yield=              'yield'
    If=                 'if'
    Elif=               'elif'
    Else=               'else'
    While=              'while'
    Break=              'break'
    Continue=           'continue'
    For=                'for'
    In=                 'in'
    Try=                'try'
    Escept=             'except'
    Finally=            'finally'
    Raise=              'raise'
    With=               'with'
    Assert=             'assert'
    Not=                'not'
    Or=                 'or'
    And=                'and'

KEYWORDS = sorted(Keyword, key=len, reverse=True)

@dataclass(eq=False, repr=False)
class Name(BaseToken):
    value: str
    hint: "Name | Literal" = None

    def __repr__(self):
        if self.hint:
            return f'Name({self.value}, {self.hint})'
        
        return f'Name({self.value})'

    @classmethod
    def scan(cls, hook: TextHook, value: str):
        for char in hook:
            if char == '_' or char >= 'a' and char <= 'z' or char >= 'A' and char <= 'Z':
                value += char
            else:
                break
        
        hook.drop()
        return cls(value)

@dataclass(eq=False)
class Literal(BaseToken):
    value: str | int | float | bool | None

    @classmethod
    def scan(cls, hook: TextHook, quote: str):
        value = str()

        for char in hook:
            hook.drop()

            if hook.test(quote):
                break
            else:
                hook.take()

            value += char

        return cls(value)
    
    @classmethod
    def scan_number(cls, hook: TextHook, value: str):
        for char in hook:
            if char == '_' or char >= '0' and char <= '9':
                value += char
            else:
                break
        
        if char != '.':
            hook.drop()
            return cls(int(value))
        
        value += char
        
        for char in hook:
            if char == '_' or char >= '0' and char <= '9':
                value += char
            else:
                hook.drop()
                break
        
        return cls(float(value))

@dataclass
class Comment(BaseToken):
    value: str

    @classmethod
    def scan(cls, hook: TextHook):
        value = str()

        for char in hook:
            if char == '\n':
                break

            value += char

        return cls(value.strip())

@dataclass
class Indent(BaseToken):
    value: int

    def __len__(self):
        return self.value

    @classmethod
    def scan(cls, hook: TextHook):
        value = 0

        for char in hook:
            if char == '\n':
                value = 0
            elif char == ' ':
                value += 1
            else:
                hook.drop()
                break

        return cls(value)

AnyToken = Token | Keyword | Name | Literal | Comment

def tokenize(stream: TextIOBase) -> TokenHook:
    def generator():
        texthook = TextHook(stream)

        for char in texthook:
            if char == ' ':
                continue
            
            if char == '\n':
                yield Indent.scan(texthook)
            elif char == '#':
                yield Comment.scan(texthook)
            
            elif char >= '0' and char <= '9':
                yield Literal.scan_number(texthook, char)
            elif char >= 'a' and char <= 'z':
                name = Name.scan(texthook, char)

                if name.value in KEYWORDS:
                    yield Keyword(name.value)
                else:
                    yield name
            elif char == '_' or char >= 'A' and char <= 'Z':
                yield Name.scan(texthook, char)
            elif char == '"' or char == "'":
                if quote := texthook.test('""', "''"):
                    yield Literal.scan(texthook, char + quote)
                else:
                    yield Literal.scan(texthook, char)
            else:
                yield Token.scan(texthook)
        
        return
    
    return TokenHook(generator())