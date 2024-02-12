# Generated by Django 4.2.1 on 2024-02-10 10:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('beats', '0014_auto_20220905_2223'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchedSong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('searched_at', models.DateTimeField(auto_now_add=True)),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beats.songs')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ListenedSong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('listened_at', models.DateTimeField(auto_now_add=True)),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beats.songs')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
