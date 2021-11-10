from decimal import Decimal
from django.core import exceptions
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


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
