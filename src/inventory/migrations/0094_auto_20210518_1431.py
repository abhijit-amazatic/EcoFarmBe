# Generated by Django 2.2 on 2021-05-18 14:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0093_summarybyproductcategory'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='summarybyproductcategory',
            unique_together={('daily_aggrigated_summary', 'product_category')},
        ),
    ]
