# Generated by Django 4.2.1 on 2023-06-01 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediksiwema', '0003_rename_ppercentage_errors_result_percentage_errors'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='actual_values',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='result',
            name='percentage_errors',
            field=models.TextField(default='[]'),
        ),
    ]
