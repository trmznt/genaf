from pyparsing import *
import sqlalchemy as sqla

# Word(initial_character_set, body_character_set)

arg = Word(alphanums + '<>=*!', alphanums + ' |&<>/*-_.,')
argname = Word(alphanums, alphanums + ':_')
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


class EvalArgExpr(QueryExpr):
    """ This is the main argument parser which provides the necessary translation
        from query text to YAML dictionary query
    """

    def __init__(self, tokens):
        print("EvalArgExpr tokens:", tokens)
        self.args = grouper(2, tokens)


    def eval(self, builder):

        dbh = builder._get_dbh()

        joined_classes = set()
        expressions = []

        for arg, field in self.args:

            if field.startswith('_'):
                raise RuntimeError('ERR: field starts with underscore: %s'
                    % field)

            field = field.lower()
            arg = arg.strip()

            try:
                func = getattr(builder, field)

            except AttributeError:
                raise RuntimeError('ERR: unknown field: %s' % field)

            expr, class_ = func( arg )
            if class_:
                joined_classes.add( class_ )
            expressions.append( expr )

        q = dbh.session().query(dbh.Sample.id)
        for class_ in joined_classes:
            q = q.join(class_)

        q = q.filter( sqla.and_( *expressions ) )
        return q



class EvalNegOp(QueryExpr):

    def __init__(self, tokens):
        print("EvalNegOp tokens:", tokens)
        self.value = tokens[0][1]

    def eval(self, builder):
        raise NotImplementedError('NegOp currently not implemented!')


class EvalSetOp(QueryExpr):

    def __init__(self, tokens):
        print("EvalSetOp tokens:", tokens)
        self.value = tokens[0]


    def eval(self, builder):
        """ return a query object
        """

        dbh = builder._get_dbh()

        tokens = self.value[1:]
        expr_1 = self.value[0].eval( builder )

        while tokens:
            op = tokens[0]
            eval_2 = tokens[1].eval( builder )
            tokens = tokens[2:]

            if op == '|':
                eval_1 = sqla.union(eval_1, eval_2)
            elif op == '&':
                eval_1 = sqla.intersect(eval_1, eval_2)
            elif op == ':':
                eval_1 = sqla.except_(
                    dbh.session().query(dbh.Sample.id).filter(
                        dbh.Sample.id.in_( sqla.union(eval_1, eval_2)) ),
                    dbh.session().query(dbh.Sample.id).filter(
                        dbh.Sample.iid.n_( sqla.intersect(eval_1, eval_2)) )
                    )

        q = dbh.session().query(dbh.Sample.id).filter( dbh.Sample.id.in_( eval_1 ) )
        return q


arg_expr.setParseAction( EvalArgExpr )

cmd_expr = operatorPrecedence( operand,
    [   (negop, 1, opAssoc.RIGHT, EvalNegOp),
        (setop, 2, opAssoc.LEFT, EvalSetOp)
    ])

#arg_expr.setParseAction( evaluate_arg_expr )


def parse_querytext(builder, text):

    expr = cmd_expr.parseString( text.strip() )
    return expr[0].eval(builder)


def query2dict( querytext ):
    """ parse querytext, returning a dictionary for selector """

    querytext = querytext.strip()
    selector = {}

    sep = querytext.count('!!')
    if sep > 1:
        raise RuntimeError('Operator !! should appear only once!')
    if sep == 1:
        common_query, split_query = querytext.split('!!')
    else:
        common_query, split_query = '', querytext

    queries = split_query.split('$')

    if len(queries) == 1:
        query = queries[0]
        if '>>' not in query:
            selector['data'] = [
                { 'query': '%s %s' % ( common_query, query) }
            ]
        else:
            query, label = query.split('>>')
            selector[ label.strip() ] = [
                { 'query': '%s %s' % ( common_query, query) }
            ]

    else:
        for query in queries:
            if '>>' not in query:
                raise RuntimeError('ERR: multiple queries must use >> operator')
            query, label = query.split('>>')
            label = label.strip()
            if label in selector:
                raise RuntimeError('ERR: duplicate label %s' % label)
            selector[label] = [
                { 'query': '%s %s' % ( common_query, query) }
            ]

    return selector

