# Generated by Django 2.1.15 on 2020-10-18 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0002_auto_20201018_1953'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseassignments',
            name='deadline',
            field=models.CharField(choices=[('passed', 'Passed'), ('active', 'Still active')], default='active', max_length=20),
        ),
    ]
