# Generated by Django 2.1.15 on 2020-12-06 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0010_courseassignments_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='is_cheated',
            field=models.BooleanField(default=False),
        ),
    ]