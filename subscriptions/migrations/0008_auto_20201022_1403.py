# Generated by Django 3.1.2 on 2020-10-22 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0007_auto_20201022_1337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermembership',
            name='volume_remaining',
            field=models.IntegerField(),
        ),
    ]
