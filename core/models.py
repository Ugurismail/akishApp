from django.db import models
from django.contrib.auth.models import User

# Soru Modeli
class Question(models.Model):
    question_text = models.TextField()  # Sorunun metni
    created_at = models.DateTimeField(auto_now_add=True)  # Oluşturulma tarihi
    updated_at = models.DateTimeField(auto_now=True)  # Son güncelleme tarihi
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Soruyu oluşturan kullanıcı
    parent_question = models.ForeignKey('self', null=True, blank=True, related_name='subquestions', on_delete=models.CASCADE)  # Alt sorular için

    def __str__(self):
        return self.question_text

    class Meta:
        ordering = ['-created_at']  # En son oluşturulan sorular ilk sırada gelir


# Yanıt Modeli
class Answer(models.Model):
    answer_text = models.TextField()  # Yanıt metni
    created_at = models.DateTimeField(auto_now_add=True)  # Oluşturulma tarihi
    updated_at = models.DateTimeField(auto_now=True)  # Son güncelleme tarihi
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Yanıtı veren kullanıcı
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)  # Yanıtın ait olduğu soru

    def __str__(self):
        return self.answer_text[:50]  # Yanıtın ilk 50 karakterini göster

    class Meta:
        ordering = ['-created_at']  # En son oluşturulan yanıtlar ilk sırada gelir
