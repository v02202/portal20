# Generated by Django 3.0.4 on 2020-03-18 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0028_merge_20200318_1145'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='status',
            field=models.CharField(choices=[('Public', 'Public'), ('Private', 'Private')], max_length=10, verbose_name='status'),
        ),
    ]
