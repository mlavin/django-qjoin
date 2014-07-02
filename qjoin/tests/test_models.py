from __future__ import unicode_literals

import re

from django.test import TestCase, SimpleTestCase
 
from .models import Person, Address, PersonAddress, Email
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

    def test_multiple_joins(self):
        """Create multiple joins."""
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


class QJoinTestCase(TestCase):
    """Use QJoin for various queries."""
