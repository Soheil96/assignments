# Generated by Django 2.1.15 on 2020-12-06 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0011_assignment_is_cheated'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='cheat_numbers',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='comment',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
