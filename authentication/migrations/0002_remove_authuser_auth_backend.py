# Generated by Django 3.0.8 on 2020-07-11 20:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authuser',
            name='auth_backend',
        ),
    ]
