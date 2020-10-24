# Generated by Django 2.1.15 on 2020-10-13 13:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploaded_files/')),
                ('uploadDate', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('ID', models.CharField(max_length=30, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('ID', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('firstName', models.CharField(max_length=100)),
                ('lastName', models.CharField(max_length=100)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='upload.Course')),
            ],
        ),
        migrations.AddField(
            model_name='assignment',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='upload.Student'),
        ),
    ]