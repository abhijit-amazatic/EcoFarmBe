# Generated by Django 2.2 on 2021-11-10 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0020_auto_20211109_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxvariable',
            name='dried_flower_tax',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Dried Flower Tax'),
        ),
        migrations.AlterField(
            model_name='taxvariable',
            name='dried_flower_tax_item',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Dried Flower Tax Item'),
        ),
        migrations.AlterField(
            model_name='taxvariable',
            name='dried_leaf_tax',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Dried Leaf Tax'),
        ),
        migrations.AlterField(
            model_name='taxvariable',
            name='dried_leaf_tax_item',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Dried Leaf Tax Item'),
        ),
    ]
