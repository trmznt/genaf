
from pyparsing import *

# Word(initial_character_set, body_character_set)

arg = Word(alphanums + '<>=*!', alphanums + ' |&<>/*-_.,')
argname = Word(alphanums, alphanums + ':')
start_bracket = Literal('[').suppress()
end_bracket = Literal(']').suppress()
arg_expr = OneOrMore( arg + start_bracket + argname + end_bracket )
set_expr = Suppress(Literal('#')) + Word(nums)
snapshot_expr = Suppress(Literal('@')) + Word(alphanums)
lpar = Literal('(').suppress()
rpar = Literal(')').suppress()
operand = arg_expr | set_expr

negop = Literal('!')   # NOT
setop = oneOf('& | :') # AND, OR, XOR


def grouper(n, iterable):
    args = [ iter(iterable)] * n
    return zip(*args)


class QueryExpr(object):

    def eval(self):
        raise NotImplemented


class Field(object):
    BATCH = 'batch'
    ID = 'id'
    CATEGORY = 'category'
    COUNTRY = 'country'
    ADMINL1 = 'adminl1'


class EvalArgExpr(QueryExpr):
    """ This is the main argument parser which provides the necessary translation
        from query text to YAML dictionary query
    """

    def __init__(self, tokens):
        print("EvalArgExpr tokens:", tokens)
        self.args = grouper(2, tokens)


    def check_field(self, field, expr):
        if field in expr:
            raise RuntimeError('Parsing query: duplicate [%s] field!' % field.upper())


    def eval(self, expr=None):
        """ this class handle the heavy-lifting of dealing with the arguments,
            if you need to add certain field please do so here
            return a dictionary
        """

        if expr is None:
            expr = {}

        for arg, field in self.args:

            field = field.lower()
            arg = arg.strip()

            try:

                if field == Field.BATCH:
                    self.check_field(Field.BATCH, expr)
                    expr[Field.BATCH] = arg
                elif field == Field.ID:
                    self.check_field(Field.ID, expr)
                    expr[Field.ID] = arg
                elif field == Field.CATEGORY:
                    self.check_field(Field.CATEGORY, expr)
                    expr[Field.CATEGORY] = arg
                elif field == Field.COUNTRY:
                    self.check_field(Field.COUNTRY, expr)
                    expr[Field.COUNTRY] = arg
                elif field == Field.ADMINL1:
                    self.check_field(Field.ADMINL1, expr)
                    expr[Field.ADMINL1] = arg

                else:
                    raise RuntimeError('Unknown field: %s' % field.upper())

            except:
                raise

        return expr


class EvalNegOp(QueryExpr):

    def __init__(self, tokens):
        print("EvalNegOp tokens:", tokens)
        self.value = tokens[0][1]

    def eval(self, expr=None):
        raise NotImplementedError('NegOp currently not implemented!')


class EvalSetOp(QueryExpr):

    def __init__(self, tokens):
        print("EvalSetOp tokens:", tokens)
        self.value = tokens[0]

    def eval(self, expr=None):
        """ return a list containing dictionaries
        """

        tokens = self.value[1:]
        expr_1 = self.value[0].eval(expr)

        expr_list = [ expr_1 ]

        while tokens:
            op = tokens[0]
            expr_2 = tokens[1].eval(expr)
            tokens = tokens[2:]

            if op == '|':
                expr_list.append( expr_2 )
            elif op == '&':
                for e in expr_list:
                    e.update( expr_2 )
            elif op == ':': # exclusive OR
                raise NotImplementedError('exclusive OR is not implemented')

        print(expr_list)
        return expr_list

arg_expr.setParseAction( EvalArgExpr )

cmd_expr = operatorPrecedence( operand,
    [   (negop, 1, opAssoc.RIGHT, EvalNegOp),
        (setop, 2, opAssoc.LEFT, EvalSetOp)
    ])

#arg_expr.setParseAction( evaluate_arg_expr )

def query2dict( querytext ):
    """ parse querytext, returning a dictionary for selector """

    querytext = querytext.strip()
    selector = {}

    if '!!' not in querytext and '$' not in querytext:
        parse_querycmd( querytext, selector )
        return selector

    if '!!' in querytext:
        if querytext.count('!!') != 1:
            raise RuntimeError('Operator !! should exist only once')

        common_query, split_query = querytext.split('!!')

    else:

        common_query, split_query = '', querytext

    common_query = common_query.strip()
    queries = split_query.split('$')

    for single_query in queries:
        parse_querycmd(single_query, selector, common_query)

    return selector


def parse_querycmd( querytext, selector, common_query=''):

    if '>>' in querytext:
        queryline, label = querytext.split('>>')
        label = label.strip()
    else:
        queryline = querytext
        label = 'all'

    if label in selector:
        raise RuntimeError('Duplicate label for sample set: %s' % label)

    if common_query:
        common_selector = cmd_expr.parseString( common_query )[0].eval()

    expr = cmd_expr.parseString( queryline.strip() )
    result = expr[0].eval()
    if type(result) == dict:
        if common_query:
            result.update( common_selector )
        result = [result]
    else:
        if common_query:
            for r in result:
                r.update( common_selector )
    selector[label] = result