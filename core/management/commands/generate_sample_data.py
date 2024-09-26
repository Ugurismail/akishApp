# core/management/commands/generate_sample_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Question, Answer
from django.utils import timezone
import random

#python manage.py generate_sample_data --users 30 --questions-per-user 10 --answers-per-question 5


class Command(BaseCommand):
    help = 'Test için örnek kullanıcılar, sorular ve yanıtlar oluşturur.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=30, help='Oluşturulacak kullanıcı sayısı')
        parser.add_argument('--questions-per-user', type=int, default=10, help='Her kullanıcı için soru sayısı')
        parser.add_argument('--answers-per-question', type=int, default=5, help='Her soru için yanıt sayısı')

    def handle(self, *args, **options):
        num_users = options['users']
        questions_per_user = options['questions_per_user']
        answers_per_question = options['answers_per_question']

        self.stdout.write(self.style.SUCCESS('Veri oluşturma işlemi başladı...'))

        # Kullanıcıları oluştur
        users = []
        for i in range(num_users):
            username = f'user_{i+1}'
            email = f'user_{i+1}@example.com'
            password = 'testpassword'
            user, created = User.objects.get_or_create(username=username, email=email)
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Kullanıcı oluşturuldu: {username}')
            users.append(user)

        # Soruları oluştur
        questions = []
        for user in users:
            for j in range(questions_per_user):
                question_text = f'Soru {j+1} - {user.username}'
                question = Question.objects.create(
                    question_text=question_text,
                    user=user,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                questions.append(question)
                self.stdout.write(f'Soru oluşturuldu: {question_text}')

        # Soruları birbirine bağla
        for question in questions:
            num_parents = random.randint(0, 3)
            parent_questions = random.sample(questions, num_parents)
            for parent in parent_questions:
                if parent != question:
                    question.parent_questions.add(parent)
            question.save()

        # Yanıtları oluştur
        for question in questions:
            answer_users = random.sample(users, min(answers_per_question, len(users)))
            for user in answer_users:
                answer_text = f'Bu yanıt {user.username} tarafından yazıldı.'
                Answer.objects.create(
                    question=question,
                    user=user,
                    answer_text=answer_text,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                self.stdout.write(f'Yanıt oluşturuldu: {user.username} - {question.question_text}')

        self.stdout.write(self.style.SUCCESS('Veri oluşturma işlemi tamamlandı!'))
