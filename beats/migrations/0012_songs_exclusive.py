# Generated by Django 3.1.6 on 2021-08-26 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beats', '0011_auto_20210112_1517'),
    ]

    operations = [
        migrations.AddField(
            model_name='songs',
            name='exclusive',
            field=models.PositiveSmallIntegerField(choices=[(1, 'free'), (2, 'paid members')], default=1),
        ),
    ]
