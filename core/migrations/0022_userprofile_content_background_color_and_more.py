# Generated by Django 4.2.2 on 2024-10-06 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_userprofile_answer_background_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='content_background_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_active_background_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_active_text_color',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_background_color',
            field=models.CharField(default='#f8f9fa', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_text_color',
            field=models.CharField(default='#000000', max_length=7),
        ),
    ]
