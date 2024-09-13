# models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import bleach

class Question(models.Model):
    question_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_questions = models.ManyToManyField('self', blank=True, related_name='subquestions', symmetrical=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    users = models.ManyToManyField(User, related_name='associated_questions', blank=True)

    def __str__(self):
        return self.question_text

    def has_subquestions(self):
        return self.subquestions.exists()

    def get_subquestions(self):
        return self.subquestions.all()

    class Meta:
        ordering = ['created_at']

# Kullanıcının tanımladığı başlangıç soruları
class StartingQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starting_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='starter_users')

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')

    ALLOWED_TAGS = ['a', 'p', 'br', 'strong', 'em']

    def __str__(self):
        return f'Answer to {self.question.question_text} by {self.user.username}'

    def save(self, *args, **kwargs):
        # Yanıt metnini güvenli hale getir
        self.answer_text = bleach.clean(
            self.answer_text,
            tags=self.ALLOWED_TAGS,
            attributes={'a': ['href', 'class']},
            strip=True
        )
        # Eğer yanıt düzenleniyorsa updated_at alanını güncelle
        if self.pk is not None:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default='#000000')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                  '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                  '#bcbd22', '#17becf']
        color = colors[instance.id % len(colors)]
        UserProfile.objects.create(user=instance, color=color)
