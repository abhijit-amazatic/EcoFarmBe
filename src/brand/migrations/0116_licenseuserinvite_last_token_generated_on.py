# Generated by Django 2.2 on 2022-03-03 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0115_remove_profilecategory_programs'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseuserinvite',
            name='last_token_generated_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
