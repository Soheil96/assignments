# Generated by Django 2.1.15 on 2020-10-19 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0004_auto_20201019_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='ID',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='student',
            name='student_id',
            field=models.CharField(max_length=20),
        ),
    ]
