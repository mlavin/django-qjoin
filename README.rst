django-qjoin
========================

Welcome to the documentation for django-qjoin!

Django-qjoin is a package that provides a way of adding arbitrary joins to a
query using expressions.

Examples
------------------------------------

Given the models::

    class Person(models.Model):
        """Simple Person model."""

        FEMALE = 'F'
        MALE = 'M'

        SEX_CHOICES = (
            (FEMALE, 'Female'),
            (MALE, 'Male'),
        )

        name = models.CharField(max_length=255)
        age = models.PositiveSmallIntegerField(default=0)
        sex = models.CharField(max_length=1, choices=SEX_CHOICES)


    class Email(models.Model):
        """A Person may have one or more emails. Emails are not necessarily tied to people."""
        email = models.EmailField()
        person = models.ForeignKey(Person, null=True)
        primary = models.BooleanField(default=False)


    class Bounce(models.Model):
        """Simple model to track an email bounce."""
        email = models.EmailField()
        bounced = models.DateTimeField(auto_now_add=True)

A simple join::

    PersonAddress.objects.filter(QJoin(person=JoinExpression(Person)))

Any join can be converted in to a left outer join::

    PersonAddress.objects.filter(QJoin(person=JoinExpression(Person, outer=True)))

Joining on a non related field::

    join = QJoin(email=JoinExpression(
        Email.objects.filter(primary=True, email='test@email.com'),
        'email')
    )
    bounces = Bounce.objects.filter(bounced__gt='2014-01-01').filter(join)

Running the Tests
------------------------------------

You can run the tests with via::

    python setup.py test

or::

    python runtests.py
