# Generated by Django 4.2.1 on 2023-05-31 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediksiwema', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InputData',
        ),
        migrations.AddField(
            model_name='result',
            name='absolute_errors',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='result',
            name='forecast_values',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='result',
            name='ppercentage_errors',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='result',
            name='actual_values',
            field=models.JSONField(),
        ),
    ]