# Generated by Django 2.1.1 on 2018-10-23 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CantoSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.CharField(max_length=255)),
                ('refresh_token', models.CharField(max_length=255)),
                ('token_valid_until', models.DateTimeField(null=True)),
                ('last_modified_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]