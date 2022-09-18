# Generated by Django 3.1.6 on 2021-08-26 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='support',
            name='issue_resolved',
            field=models.CharField(choices=[(1, 'Issue unresolved'), (2, 'Pending'), (3, 'Issue Resolved')], default=1, max_length=100),
        ),
    ]