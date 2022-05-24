from dataclasses import dataclass

from .tokenizer import BINARY_OPERATORS, UNARY_OPERATORS
from .tokenizer import TokenHook, Token, Keyword, Name, Literal, Indent, Comment

@dataclass
class Call:
    head: "Operand"
    args: list["Operand"]

    @classmethod
    def parse(cls, hook: TokenHook, head: "Operand"):
        args = []

        for token in hook:
            if token is Token.RightParenthesis:
                break

            expression = BinaryOperation.parse(hook, token, {Token.Comma, Token.RightParenthesis})
            args.append(expression)

            token = hook.take()

            if token is Token.RightParenthesis:
                break
            elif token is Token.Comma:
                continue
            else:
                raise SyntaxError(f"expecting ',' or ')', found {token}")

        return cls(head, args)

@dataclass
class UnaryOperation:
    operator: Token
    operand: "Operand"

@dataclass
class BinaryOperation:
    operator: Token
    left: "Operand"
    right: "Operand"

    @classmethod
    def parse(cls, hook: TokenHook, operand: "Operand", ignore=set()) -> "Operand":
        operator = hook.take()

        if operator is None:
            return operand
        elif type(operator) is Indent or operator in ignore or type(operator) in ignore:
            hook.drop()
            return operand

        if operand in UNARY_OPERATORS:
            return UnaryOperation(operand, operator)

        elif operator is Token.LeftParenthesis:
            return Call.parse(hook, operand)
        
        elif operator not in BINARY_OPERATORS:
            raise SyntaxError(f'unexpected operator {operator}')

        return cls(operator, operand, cls.parse(hook,  hook.take(), ignore))

Operand = Name | Literal | UnaryOperation | BinaryOperation | Call

@dataclass
class Set:
    name: Name
    value: Operand

@dataclass
class Body:
    lines: list[Operand]

    @classmethod
    def parse(cls, hook: TokenHook):
        token = hook.take()

        if token is not Token.Colon:
            raise SyntaxError(f"expecting ':', found {token}")

        indent = hook.take()
        lines = [] 

        for token in hook:
            if type(token) is Indent:
                if token.value < indent.value:
                    hook.drop()
                    break
                else:
                    continue

            if token is Token.Ellipsis:
                lines.append(token)
            elif token is Keyword.Def:
                lines.append(Def.parse(hook))
            elif token is Keyword.Return:
                lines.append(Return.parse(hook))
            elif token is Keyword.If:
                lines.append(If.parse(hook))
            elif token is Keyword.Elif:
                lines.append(Elif.parse(hook))
            elif token is Keyword.Else:
                lines.append(Else.parse(hook))
            elif token is Keyword.While:
                lines.append(While.parse(hook))
            elif token is Keyword.With:
                lines.append(With.parse(hook))
            
            elif type(token) is Name:
                name = token
                token = hook.take()

                if token is Token.Colon:
                    name.hint = BinaryOperation.parse(hook, hook.take(), {Token.Equal})
                    token = hook.take()
                
                if token is Token.Equal:
                    lines.append(Set(name, BinaryOperation.parse(hook, hook.take())))
                else:
                    hook.drop()
                    lines.append(BinaryOperation.parse(hook, name))
            else:
                lines.append(BinaryOperation.parse(hook, token))
        
        return cls(lines)

@dataclass
class Return:
    value: Operand

    @classmethod
    def parse(cls, hook: TokenHook):
        return cls(BinaryOperation.parse(hook, hook.take()))

@dataclass
class Import(Return):
    pass

@dataclass
class From:
    head: Operand
    args: list[Name]

    @classmethod
    def parse(cls, hook: TokenHook):
        head = hook.take()
        args = []

        token = hook.take()

        if token is not Keyword.Import:
            raise SyntaxError(f"expecting 'import', found {token}")

        for token in hook:
            if type(token) is Indent:
                break

            if type(token) is Name:
                args.append(token)
                token = hook.take()

                if type(token) is Indent:
                    break
                elif token is Token.Comma:
                    continue
                else:
                    raise SyntaxError(f"expecting ',', found {token}")
            else:
                raise SyntaxError(f"expecting name, found {token}")
        
        hook.drop()

        return cls(head, args)

@dataclass
class If:
    head: Operand
    body: Body

    @classmethod
    def parse(cls, hook: TokenHook):
        return cls(BinaryOperation.parse(hook, hook.take(), {Token.Colon}), Body.parse(hook))

@dataclass
class Elif(If):
    pass

@dataclass
class While(If):
    pass

@dataclass
class Else:
    body: Body

    @classmethod
    def parse(cls, hook: TokenHook):
        return cls(Body.parse(hook))
    
@dataclass
class With(If):
    pass

@dataclass
class Def:
    name: Name
    head: list[Name]
    body: list[Operand]
    hint: "Name | Literal"=None

    @classmethod
    def parse(cls, hook: TokenHook):
        name = hook.take()

        if type(name) is not Name:
            raise TypeError(f'expecting a name, found {name}')
        
        token = hook.take()

        if token is not Token.LeftParenthesis:
            raise SyntaxError(f"expecting '(', found {token}")
        
        head = []

        for token in hook:
            if token is Token.RightParenthesis:
                break
            elif type(token) is not Name:
                raise TypeError(f'expecting a name, found {token}')
            
            pname = token
            token = hook.take()

            if token is Token.Colon:
                pname.hint = BinaryOperation.parse(hook, hook.take(), {Token.Comma, Token.RightParenthesis})
                token = hook.take()

            head.append(pname)

            if token is Token.Comma:
                continue
            elif token is Token.RightParenthesis:
                break
            else:
                raise SyntaxError(f"expecting ',', found {token}")
        
        token = hook.take()

        if token is Token.Arrow:
            hint = BinaryOperation.parse(hook, hook.take(), {Token.Colon})
        else:
            hint = None
            hook.drop()
                
        return cls(name, head, Body.parse(hook), hint)


@dataclass
class Class:
    name: Name
    head: list[Name]
    body: list[Operand]

    @classmethod
    def parse(cls, hook: TokenHook):
        name = hook.take()

        if type(name) is not Name:
            raise TypeError(f'expecting a name, found {name}')
        
        token = hook.take()
        head = []

        if token is Token.LeftParenthesis:
            for token in hook:
                if token is Token.RightParenthesis:
                    break
                elif type(token) is not Name:
                    raise TypeError(f'expecting a name, found {token}')
                
                head.append(token)
                token = hook.take()

                if token is Token.Colon:
                    continue
                elif token is Token.RightParenthesis:
                    break
                else:
                    raise SyntaxError(f"expecting ',', found {token}")
        else:
            hook.drop()
                
        return cls(name, head, Body.parse(hook))

def parse(hook: TokenHook):
    for token in hook:
        if type(token) is Indent:
            continue
        elif type(token) is Comment:
            yield token
            continue

        if type(token) is Name:
            name = token
            token = hook.take()

            if token is Token.Colon:
                name.hint = BinaryOperation.parse(hook, hook.take(), {Token.Equal})
                token = hook.take()

            if token is Token.Equal:
                yield Set(name, BinaryOperation.parse(hook, hook.take()))
            else:
                hook.drop()
                yield BinaryOperation.parse(hook, name)

        elif token is Keyword.Def:
            yield Def.parse(hook)
        elif token is Keyword.Class:
            yield Class.parse(hook)
        elif token is Keyword.Import:
            yield Import.parse(hook)
        elif token is Keyword.From:
            yield From.parse(hook)
        elif token is Keyword.If:
            yield If.parse(hook)
        elif token is Keyword.Elif:
            yield Elif.parse(hook)
        elif token is Keyword.Else:
            yield Else.parse(hook)
        else:
            yield BinaryOperation.parse(hook, token, {Keyword, Indent})
    
    return