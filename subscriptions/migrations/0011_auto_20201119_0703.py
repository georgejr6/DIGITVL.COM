# Generated by Django 3.1.3 on 2020-11-19 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0010_merge_20201105_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='storage_size',
            field=models.IntegerField(default=10800),
        ),
        migrations.AlterField(
            model_name='usermembership',
            name='volume_remaining',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
