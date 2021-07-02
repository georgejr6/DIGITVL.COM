# Generated by Django 3.1.5 on 2021-01-20 20:25

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_user_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(db_index=True, max_length=100, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()]),
        ),
    ]
