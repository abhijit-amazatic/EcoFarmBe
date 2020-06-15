# Generated by Django 2.2 on 2020-06-15 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_auto_20200612_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='cf_alpha_humulene',
            field=models.FloatField(blank=True, null=True, verbose_name='ALPHA HUMULENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_alpha_pinene',
            field=models.FloatField(blank=True, null=True, verbose_name='ALPHA PIENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_alpha_terpineol',
            field=models.FloatField(blank=True, null=True, verbose_name='ALPHA TERPINEOL'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_beta_caryophyllene',
            field=models.FloatField(blank=True, null=True, verbose_name='BETA CARYOPHYLLENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_geraniol',
            field=models.FloatField(blank=True, null=True, verbose_name='GERANIOL'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_linalool',
            field=models.FloatField(blank=True, null=True, verbose_name='LINALOOL'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_myrcene',
            field=models.FloatField(blank=True, null=True, verbose_name='MYRECENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_ocimene',
            field=models.FloatField(blank=True, null=True, verbose_name='OCIMENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_r_limonene',
            field=models.FloatField(blank=True, null=True, verbose_name='LIMONENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_terpinolene',
            field=models.FloatField(blank=True, null=True, verbose_name='TERPINOLENE'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_valencene',
            field=models.FloatField(blank=True, null=True, verbose_name='VALENECENE'),
        ),
    ]
