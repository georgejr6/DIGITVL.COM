# Generated by Django 3.1.6 on 2021-02-09 18:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='blogs',
            old_name='blog_slug',
            new_name='slug',
        ),
    ]
