# Generated by Django 3.2.5 on 2021-08-05 13:29

from django.db import migrations, models
import nollesystemet.models.misc


class Migration(migrations.Migration):

    dependencies = [
        ('nollesystemet', '0011_nollegroup_group_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drinkoption',
            name='drink',
            field=models.CharField(max_length=100, validators=[nollesystemet.models.misc.validate_no_emoji]),
        ),
        migrations.AlterField(
            model_name='extraoption',
            name='extra_option',
            field=models.CharField(max_length=100, validators=[nollesystemet.models.misc.validate_no_emoji]),
        ),
    ]
