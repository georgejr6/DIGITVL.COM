# Generated by Django 3.1.5 on 2021-01-22 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_remove_user_blue_tick_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='blue_tick_verified',
            field=models.BooleanField(default=False),
        ),
    ]
