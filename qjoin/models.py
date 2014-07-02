from copy import deepcopy

from django.db.models import Q
from django.db.models.expressions import ExpressionNode
from django.db.models.fields.related import RelatedField
from django.db.models.query import QuerySet


class NoOpCompiler(object):
    """No-op subquery SQL compiler."""

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

    def __init__(self, qs_or_model, rhs_column='id', outer=False):
        super(JoinExpression, self).__init__(None, None, False)
        self.rhs_column = rhs_column
        self.name = None
        self.outer = outer
        if isinstance(qs_or_model, QuerySet):
            self.rhs_query = qs_or_model.query
            self.rhs_model = self.rhs_query.model
        else:
            self.rhs_query = None
            self.rhs_model = qs_or_model

    def __repr__(self):
        return '<JoinExpression: %s %s %s.%s>' % (self.name,
            'OUTER' if self.outer else 'INNER', self.rhs_model._meta.db_table,
            self.rhs_column)

    def contains_aggregate(self, existing_aggregates):
        return False

    def _get_column(self, model, name):
        for field in model._meta.fields:
            if field.name == name:
                _, column = field.get_attname_column()
                return column
        raise ValueError('Invalid field "%s" for %s' % (name, model.__name__))

    def prepare(self, evaluator, query, allow_joins):
        lhs_model = query.model
        lhs_column = self._get_column(lhs_model, self.name)
        rhs_column = self._get_column(self.rhs_model, self.rhs_column)
        connection = (
            lhs_model._meta.db_table,
            self.rhs_model._meta.db_table,
            ((lhs_column, rhs_column), )
        )
        query.get_initial_alias()
        query.join(connection, outer_if_first=self.outer, join_field=QueryFieldRestriction(self.rhs_query))

        if isinstance(query.get_meta().get_field(self.name), RelatedField):
            evaluator.get_compiler = self.get_compiler
        else:
            # When dealing with a non-fk, it's necessary to have the evaluator
            # return the table.column because the ORM adds "table.column = " to
            # the where clause. This essentially results in a no-op and will be
            # removed by any database's query optimizer.
            def as_sql(qn, connection):
                return '%s.%s' % (qn(lhs_model._meta.db_table), qn(lhs_column)), []
            evaluator.as_sql = as_sql

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
