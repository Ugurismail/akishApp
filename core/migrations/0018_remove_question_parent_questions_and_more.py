# Generated by Django 4.2.2 on 2024-09-30 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_userprofile_invitation_quota_invitation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='parent_questions',
        ),
        migrations.AddField(
            model_name='question',
            name='subquestions',
            field=models.ManyToManyField(blank=True, related_name='parent_questions', to='core.question'),
        ),
    ]
