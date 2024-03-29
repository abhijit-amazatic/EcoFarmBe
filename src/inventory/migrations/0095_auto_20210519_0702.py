# Generated by Django 2.2 on 2021-05-19 07:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0094_auto_20210518_1431'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[("DELETE FROM inventory_inventoryitemdelist where item_id is null;", None)],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='inventoryitemdelist',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deletion_requests', to='inventory.Inventory', verbose_name='item'),
        ),
    ]
