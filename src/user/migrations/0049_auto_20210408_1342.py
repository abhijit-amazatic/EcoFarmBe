# Generated by Django 2.2 on 2021-04-08 13:42

from django.db import migrations
import user.models
from user.models import generate_unique_user_id

def generate_unique_id(apps, schema_editor):
    User = apps.get_model("user", "User")
    for user in User.objects.all():
        user.unique_user_id = generate_unique_user_id()
        user.save(update_fields=['unique_user_id'])

    
def generate_unique_id_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0048_user_unique_user_id'),
    ]

    operations = [
         migrations.RunPython(generate_unique_id, reverse_code=generate_unique_id_reverse),    
    ]
