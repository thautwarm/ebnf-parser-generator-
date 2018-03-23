from calc_oppt_parser import (AstParser, token_func, arith, UNameEnum, Tokenizer)

from Ruikowa.ObjectRegex.ASTDef import Ast
from Ruikowa.ErrorHandler import ErrorHandler
from numbers import Real

from typing import (Optional, Iterable, Generic, TypeVar, Iterator)
from collections import Iterable as CIterable
from functools import reduce
from toolz import curry

import operator

T = TypeVar('T')

src_code_token_parse = ErrorHandler(arith.match, token_func).from_source_code

op_priorities = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "//": 2
}
op_func = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv
}


def parse(src: str) -> Ast:
    filename = '<my calculator>'
    return src_code_token_parse(filename, src)


def flatten(seq):
    for each in seq:
        if isinstance(each, CIterable) and not isinstance(each, str):
            yield from flatten(each)
        yield each


def ast_for_decimal(decimal: Ast) -> Real:
    return eval(''.join(map(lambda _: _.string, flatten(decimal))))


def ast_for_arith(arith: Ast) -> Real:
    if len(arith) is 1:
        return ast_for_factor(arith[0])
    return visit_bin_expr(lambda _: ast_for_factor(_) if _.__class__ is Ast else _, DoublyList.from_iter(arith))


def ast_for_factor(factor: Ast) -> Real:
    if len(factor) is 2:
        s, atom = factor
        return -ast_for_atom(atom) if s.string is '-' else ast_for_atom(atom)
    return ast_for_atom(factor[0])


def ast_for_atom(atom: Ast) -> Real:
    if atom[0].name is UNameEnum.decimal:
        return ast_for_decimal(atom[0])
    return ast_for_arith(atom[1])


class DoublyList(Iterable, Generic[T]):

    def __init__(self, content: T, prev: 'Optional[DoublyList[T]]' = None, next: 'Optional[DoublyList]' = None):
        self.content: T = content
        self.next = next
        self.prev = prev

    def __iter__(self) -> 'Iterator[DoublyList[T]]':
        yield self
        if self.next:
            yield from self.next

    def __str__(self):
        return f'[{self.content}{self.next}]'

    __repr__ = __str__

    @classmethod
    def from_iter(cls, iterable: 'Iterable') -> 'Optional[DoublyList]':
        if not iterable:
            return None
        s_iterable = iter(iterable)
        try:
            fst = cls(next(s_iterable))
        except StopIteration:
            return None

        reduce(lambda a, b: setattr(a, "next", cls(b)) or setattr(a.next, "prev", a) or a.next, s_iterable, fst)
        return fst


@curry
def fmap(t, func):
    return lambda *args: func(*map(t, args))


def visit_bin_expr(func, seq: 'DoublyList[AstParser]'):
    def sort_by_func(e: 'DoublyList[Tokenizer]'):
        return op_priorities[e.content.string]

    functor = fmap(func)

    op_nodes = (each for each in seq if each.content.name is not UNameEnum.factor)
    op_nodes: DoublyList[Tokenizer] = sorted(op_nodes, key=sort_by_func, reverse=True)

    for each in op_nodes:
        bin_expr = functor(op_func[each.content.string])(each.prev.content, each.next.content)
        each.content = bin_expr
        try:
            each.prev.prev.next = each
            each.prev = each.prev.prev
        except AttributeError:
            pass

        try:
            each.next.next.prev = each
            each.next = each.next.next
        except AttributeError:
            pass

    each: DoublyList[Real]
    return each.content


def repl():
    while True:
        try:
            inp = input('my_calc:: ')
            print(ast_for_arith(parse(inp)))
        except KeyboardInterrupt:
            print('\nbye')
            import sys
            sys.exit(0)


if __name__ == '__main__':
    repl()
