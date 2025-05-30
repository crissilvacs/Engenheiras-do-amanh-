# Generated by Django 5.2 on 2025-04-17 17:54

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comunidade', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100)),
                ('conteudo', models.TextField()),
                ('autor', models.CharField(max_length=100)),
                ('data_criacao', models.DateField(default=django.utils.timezone.now)),
            ],
        ),
    ]
