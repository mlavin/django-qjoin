from __future__ import unicode_literals

import re

from django.test import TestCase, SimpleTestCase
 
from .models import Person, Address, PersonAddress, Email, Bounce
from ..models import QJoin, JoinExpression
 
 
class QJoinSQLTestCase(SimpleTestCase):
    """Checking for the expected SQL generation."""

    maxDiff = None

    def _clean_sql(self, sql):
        return re.sub(r'\s+', ' ', sql).strip()

    def assertQueryEqual(self, qs, sql):
        """Clean up newlines and leading spaces for asserting the SQL."""
        result = self._clean_sql(str(qs.query))
        expected = self._clean_sql(sql)
        self.assertEqual(result, expected)
 
    def test_simple_join(self):
        """Build basic join."""
        expression = JoinExpression(Person)
        join = QJoin(person=expression)
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id",
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM
            "tests_personaddress" INNER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" )
        ''')

    def test_simple_louter_join(self):
        """Build basic left outer join."""
        expression = JoinExpression(Person, outer=True)
        join = QJoin(person=expression)
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id", 
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM 
            "tests_personaddress" LEFT OUTER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" )
        ''')

    def test_filtered_join(self):
        """Build inner join with filter."""
        expression = JoinExpression(Person.objects.filter(age__gt=10))
        join = QJoin(person=expression)
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id", 
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM 
            "tests_personaddress" INNER JOIN "tests_person" ON ( 
                "tests_personaddress"."person_id" = "tests_person"."id" AND ("tests_person"."age" > 10 ))
        ''')

    def test_filtered_outer_join(self):
        """Build outer join with filter."""
        expression = JoinExpression(Person.objects.filter(age__gt=10), outer=True)
        join = QJoin(person=expression)
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id",
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM
            "tests_personaddress" LEFT OUTER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" AND ("tests_person"."age" > 10 ))
        ''')

    def test_complex_qs_join(self):
        """Build a join on a queryset with other filters."""
        expression = JoinExpression(Person)
        join = QJoin(person=expression)
        query = PersonAddress.objects.filter(join, primary=True)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id",
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM
            "tests_personaddress" INNER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" )
            WHERE "tests_personaddress"."primary" = True
        ''')

    def test_complex_qs_outer_join(self):
        """Build an outer join on a queryset with other filters."""
        expression = JoinExpression(Person, outer=True)
        join = QJoin(person=expression)
        query = PersonAddress.objects.filter(join, primary=True)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id", 
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM 
            "tests_personaddress" LEFT OUTER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" ) 
            WHERE "tests_personaddress"."primary" = True 
        ''')

    def test_multiple_inner_joins(self):
        """Create multiple inner joins."""
        join = QJoin(person=JoinExpression(Person), address=JoinExpression(Address))
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id",
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM
            "tests_personaddress" INNER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" )
            INNER JOIN "tests_address" ON (
                "tests_personaddress"."address_id" = "tests_address"."id" )
        ''')

    def test_multiple_outer_joins(self):
        """Create multiple outer joins."""
        join = QJoin(person=JoinExpression(Person, outer=True), address=JoinExpression(Address, outer=True))
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id", 
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM 
            "tests_personaddress" LEFT OUTER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" ) 
            LEFT OUTER JOIN "tests_address" ON (
                "tests_personaddress"."address_id" = "tests_address"."id" )
        ''')

    def test_multiple_mixed_joins(self):
        """Create multiple joins using outer and inner joins."""
        join = QJoin(person=JoinExpression(Person, outer=True), address=JoinExpression(Address, outer=False))
        query = PersonAddress.objects.filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_personaddress"."id", "tests_personaddress"."person_id",
            "tests_personaddress"."address_id", "tests_personaddress"."primary" FROM
            "tests_personaddress" LEFT OUTER JOIN "tests_person" ON (
                "tests_personaddress"."person_id" = "tests_person"."id" )
            INNER JOIN "tests_address" ON (
                "tests_personaddress"."address_id" = "tests_address"."id" )
        ''')

    def test_non_fk_inner_join(self):
        """Create an inner join between non-FK fields."""
        join = QJoin(email=JoinExpression(Email.objects.filter(primary=True, email='a'), 'email'))
        query = Bounce.objects.filter(bounced__gt='2014-01-01').filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_bounce"."id", "tests_bounce"."email",
            "tests_bounce"."bounced" FROM "tests_bounce" INNER JOIN
            "tests_email" ON ( "tests_bounce"."email" = "tests_email"."email"
                AND (("tests_email"."primary" = True AND "tests_email"."email" = a )))
            WHERE ("tests_bounce"."bounced" > 2014-01-01 00:00:00 AND
                "tests_bounce"."email" = "tests_bounce"."email")
        ''')

    def test_non_fk_outer_join(self):
        """Create an inner join between non-FK fields."""
        join = QJoin(email=JoinExpression(Email.objects.filter(primary=True, email='a'), 'email', outer=True))
        query = Bounce.objects.filter(bounced__gt='2014-01-01').filter(join)
        self.assertQueryEqual(query, '''
            SELECT "tests_bounce"."id", "tests_bounce"."email",
            "tests_bounce"."bounced" FROM "tests_bounce" LEFT OUTER JOIN
            "tests_email" ON ( "tests_bounce"."email" = "tests_email"."email"
                AND (("tests_email"."primary" = True AND "tests_email"."email" = a )))
            WHERE ("tests_bounce"."bounced" > 2014-01-01 00:00:00 AND
                "tests_bounce"."email" = "tests_bounce"."email")
        ''')

class QJoinTestCase(TestCase):
    """Use QJoin for various queries."""
