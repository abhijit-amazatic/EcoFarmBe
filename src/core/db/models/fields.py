from decimal import Decimal
from django.contrib.postgres.fields import citext
from django.core import exceptions
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.six import with_metaclass

# Custom lowecase CharField

class CaseInsensitiveEmailField(models.EmailField):
    """
    Case-insensitive email field.
    """
    LOOKUP_REPLACE = {
        'exact': 'iexact',
        'contains': 'icontains',
        'startswith': 'istartswith',
        'endswith': 'iendswith',
        'regex': 'iregex',
    }

    def get_lookup(self, lookup_name):
        return super().get_lookup(self.LOOKUP_REPLACE.get(lookup_name, lookup_name))

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if isinstance(value, str):
            return value.lower()
        return value

    def to_python(self, value):
        value = super().to_python(value)
        if isinstance(value, str):
            return value.lower()
        return value

class PercentField(models.FloatField):
    """
    Float field that ensures field value is in the range 0-100.
    """
    default_validators = [
        MinValueValidator(0),
        MaxValueValidator(100),
    ]

    def formfield(self, **kwargs):
        return super().formfield(**{
            'min_value': 0,
            'max_value': 100,
            **kwargs,
        })


class PositiveDecimalField(models.DecimalField):
    """
    Float field that ensures field value is in the range 0-100.
    """
    default_validators = [
        MinValueValidator(Decimal('0')),
    ]

    def formfield(self, **kwargs):
        return super().formfield(**{
            'min_value': 0,
            **kwargs,
        })
