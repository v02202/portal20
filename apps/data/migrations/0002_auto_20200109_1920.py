# Generated by Django 3.0.1 on 2020-01-09 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dataset',
            old_name='organization_id',
            new_name='organization',
        ),
        migrations.AlterField(
            model_name='dataset',
            name='status',
            field=models.CharField(choices=[('Private', 'Private'), ('Public', 'Public')], max_length=10, verbose_name='status'),
        ),
    ]
