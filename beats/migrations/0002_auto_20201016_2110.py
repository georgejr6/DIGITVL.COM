# Generated by Django 3.1.2 on 2020-10-16 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beats', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='songs',
            name='audio_file',
            field=models.FileField(upload_to='songs/%Y/%m/%d/'),
        ),
    ]