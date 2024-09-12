from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Question(models.Model):
    question_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Bir soru birden fazla ana soruya bağlanabilir (Many-to-Many)
    parent_questions = models.ManyToManyField('self', blank=True, related_name='subquestions', symmetrical=False)

    # Soruyu soran kullanıcı
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return self.question_text

    def has_subquestions(self):
        return self.subquestions.exists()

    def get_subquestions(self):
        return self.subquestions.all()

    class Meta:
        ordering = ['created_at']  # Soruları en son eklenen sırasına göre sıralar

# Kullanıcının tanımladığı başlangıç soruları
class StartingQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starting_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='starter_users')

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"

# Yanıt Modeli


from django.utils import timezone

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)  # Boş değerlere izin ver
 # auto_now özelliğini kaldırdık

    # Yanıtı veren kullanıcı
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')

    def __str__(self):
        return f'Answer to {self.question.question_text} by {self.user.username}'

    def save(self, *args, **kwargs):
        # Eğer yanıt düzenleniyorsa updated_at alanını güncelle
        if self.pk is not None:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
