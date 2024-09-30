from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import bleach


class Question(models.Model):
    question_text = models.CharField(max_length=255)
    subquestions = models.ManyToManyField('self', symmetrical=False, related_name='parent_questions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # parent_questions alanını kaldırdık
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    users = models.ManyToManyField(
        User, related_name='associated_questions', blank=True
    )
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    def __str__(self):
        return self.question_text

    def has_subquestions(self):
        return self.subquestions.exists()

    def get_subquestions(self):
        return self.subquestions.all()

    def get_total_subquestions_count(self, visited=None):
        if visited is None:
            visited = set()
        if self.id in visited:
            return 0
        visited.add(self.id)
        count = 0
        for subquestion in self.subquestions.all():
            count += 1  # Doğrudan alt soruyu say
            count += subquestion.get_total_subquestions_count(visited)  # Alt soruların alt sorularını say
        return count

    class Meta:
        ordering = ['created_at']


# Kullanıcının tanımladığı başlangıç soruları
class StartingQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starting_questions')
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='starter_users'
    )

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    ALLOWED_TAGS = ['a', 'p', 'br', 'strong', 'em']

    def __str__(self):
        return f"Answer to {self.question.question_text} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Clean the answer_text to make it safe
        self.answer_text = bleach.clean(
            self.answer_text,
            tags=self.ALLOWED_TAGS,
            attributes={'a': ['href', 'class']},
            strip=True
        )
        # Update the updated_at field if editing
        if self.pk is not None:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default='#000000')
    invitation_quota = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Profili"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Kullanıcıya bir renk atayın
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                  '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                  '#bcbd22', '#17becf']
        color = colors[instance.id % len(colors)]
        # Süper kullanıcıya sınırsız davet hakkı ver
        if instance.is_superuser:
            invitation_quota = 99999999  # Veya çok yüksek bir sayı
        else:
            invitation_quota = 0  # Normal kullanıcılar için başlangıç davet hakkı
        UserProfile.objects.create(user=instance, color=color, invitation_quota=invitation_quota)
class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, null=True, blank=True
    )
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, null=True, blank=True
    )
    value = models.IntegerField()  # +1 veya -1

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'], name='unique_user_question_vote'
            ),
            models.UniqueConstraint(
                fields=['user', 'answer'], name='unique_user_answer_vote'
            ),
        ]

class SavedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, null=True, blank=True
    )
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, null=True, blank=True
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question', 'answer')

class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages'
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject}"

class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_invitations', null=True, blank=True
    )
    recipient_email = models.EmailField()
    quota_granted = models.PositiveIntegerField(default=0)
    is_accepted = models.BooleanField(default=False)
    accepted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='accepted_invitations', null=True, blank=True
    )
    sent_at = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Davet {self.recipient_email} - Gönderen: {self.sender.username if self.sender else 'Sistem'}"
