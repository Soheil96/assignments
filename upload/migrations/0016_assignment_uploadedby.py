# Generated by Django 2.1.15 on 2021-03-30 07:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0015_auto_20210330_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='uploadedBy',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='upload.Student'),
        ),
    ]