from django.contrib.auth.models import User
from django.db import models
 


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


class Address(models.Model):
    """Simple Address model."""
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)


class PersonAddress(models.Model):
    """Many to Many through table between Person and Address."""
    person = models.ForeignKey(Person)
    address = models.ForeignKey(Address)
    primary = models.BooleanField(default=False)


class Email(models.Model):
    """A Person may have one or more emails. Emails are not necessarily tied to people."""
    email = models.EmailField()
    person = models.ForeignKey(Person, null=True)
    primary = models.BooleanField(default=False)


class Bounce(models.Model):
    """Simple model to track an email bounce."""
    email = models.EmailField()
    bounced = models.DateTimeField(auto_now_add=True)
