from copy import deepcopy

from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.expressions import ExpressionNode


class NoOpCompiler(object):
    """No-op subquery SQL compiler."""

    def as_sql(self, *args, **kwargs):
        return '', []

    def as_subquery_condition(self, *args, **kwargs):
        return '', []


class QueryFieldRestriction(object):

    def __init__(self, query):
        self.query = query and query.clone()

    def get_extra_restriction(self, where_class, alias, lhs):
        if self.query is not None:
            self.query.where.relabel_aliases({self.query.tables[0]: alias})
            return self.query.where
        else:
            return None


class JoinExpression(ExpressionNode):
    """Builds a join expression to be fed into a QJoin."""

    def __init__(self, qs_or_model, rhs_column='id'):
        super(JoinExpression, self).__init__(None, None, False)
        self.rhs_column = rhs_column
        self.name = None
        if isinstance(qs_or_model, QuerySet):
            self.rhs_query = qs_or_model.query
            self.rhs_model = self.rhs_query.model
        else:
            self.rhs_query = None
            self.rhs_model = qs_or_model

    def contains_aggregate(self, existing_aggregates):
        return False

    def _get_column(self, model, name):
        for field in model._meta.fields:
            if field.name == name:
                _, column = field.get_attname_column()
                return column
        raise ValueError('Invalid field "%s" for %s' % (name, model.__name__))

    def prepare(self, evaluator, query, allow_joins):
        evaluator.get_compiler = self.get_compiler
        lhs_model = query.model
        lhs_column = self._get_column(lhs_model, self.name)
        rhs_column = self._get_column(self.rhs_model, self.rhs_column)
        connection = (
            lhs_model._meta.db_table,
            self.rhs_model._meta.db_table,
            ((lhs_column, rhs_column), )
        )
        query.get_initial_alias()
        query.join(connection, join_field=QueryFieldRestriction(self.rhs_query))
        return evaluator.prepare_leaf(self, query, allow_joins)
        
    def evaluate(self, evaluator, qn, connection):
        return evaluator.evaluate_leaf(self, qn, connection)

    def get_compiler(self, *args, **kwargs):
        return NoOpCompiler()


class QJoin(Q):
    """Custom Q which takes a JoinExpression to add a join to the current query."""

    def __init__(self, **kwargs):
        for column, expression in kwargs.items():
            expression.name = column
        super(QJoin, self).__init__( **kwargs)
