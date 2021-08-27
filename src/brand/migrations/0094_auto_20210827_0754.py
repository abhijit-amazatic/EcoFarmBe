# Generated by Django 2.2 on 2021-08-27 07:54


import random
import brand.models
from django.db import migrations, models


def generate_random_number(length=6):
    rand = random.SystemRandom()
    digits = [rand.choice('123456789'),]
    if hasattr(rand, 'choices'):
        digits += rand.choices('0123456789', k=length-1)
    else:
        digits += (rand.choice('0123456789') for i in range(length-1))

    return int(''.join(digits))

def get_client_id(model):
    c_id = generate_random_number(length=6)
    try:
        model.objects.get(client_id=c_id)
    except model.DoesNotExist:
        return c_id
    except Exception as e:
        print(e)
        return get_client_id(model)
    else:
        return get_client_id(model)


def forward_func(apps, schema_editor):
    License = apps.get_model("brand", "License")
    for obj in License.objects.all():
        obj.client_id = generate_random_number(length=6)
        obj.save()

def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0093_license_client_id'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_code=reverse_func),
        migrations.AlterField(
            model_name='license',
            name='client_id',
            field=models.PositiveIntegerField(help_text='Randomly genrated 6 digit number.', unique=True, validators=[brand.models.client_id_validator]),
        ),
    ]
