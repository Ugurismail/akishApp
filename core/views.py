from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .models import Question, Answer
from .forms import QuestionForm, AnswerForm, CustomLoginForm

# Ana sayfa: Ana soruları listele
def question_list(request):
    questions = Question.objects.filter(parent_question=None)  # Sadece ana soruları getir
    return render(request, 'core/question_list.html', {'questions': questions})

def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.all()  # Soruya bağlı yanıtları al
    subquestions = question.subquestions.all()  # Soruya bağlı alt soruları al
    return render(request, 'core/question_detail.html', {
        'question': question,
        'answers': answers,
        'subquestions': subquestions
    })
# Soru ekleme
@login_required
def add_question(request):
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_form = AnswerForm(request.POST)
        if question_form.is_valid() and answer_form.is_valid():
            question = question_form.save(commit=False)
            question.user = request.user  # Soruyu soran kullanıcıyı ekle
            question.save()

            answer = answer_form.save(commit=False)
            answer.user = request.user  # Yanıtı veren kullanıcıyı ekle
            answer.question = question  # Yanıtı soruya bağla
            answer.save()

            return redirect('question_list')  # Ana sayfaya yönlendir
    else:
        question_form = QuestionForm()
        answer_form = AnswerForm()

    return render(request, 'core/add_question.html', {
        'question_form': question_form,
        'answer_form': answer_form,
    })

# Alt soru ekleme
@login_required
def add_subquestion(request, question_id):
    parent_question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_form = AnswerForm(request.POST)
        if question_form.is_valid() and answer_form.is_valid():
            subquestion = question_form.save(commit=False)
            subquestion.parent_question = parent_question
            subquestion.user = request.user
            subquestion.save()

            # İlk yanıtı kaydet
            answer = answer_form.save(commit=False)
            answer.question = subquestion
            answer.user = request.user
            answer.save()

            return redirect('question_detail', question_id=parent_question.id)
    else:
        question_form = QuestionForm()
        answer_form = AnswerForm()

    return render(request, 'core/add_subquestion.html', {
        'parent_question': parent_question,
        'question_form': question_form,
        'answer_form': answer_form
    })

# Yanıt düzenleme
@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST, instance=answer)
        if answer_form.is_valid():
            answer_form.save()
            return redirect('question_detail', question_id=answer.question.id)
    else:
        answer_form = AnswerForm(instance=answer)

    return render(request, 'core/edit_answer.html', {'answer_form': answer_form})

# Profil görüntüleme
@login_required
def profile(request):
    return render(request, 'core/profile.html', {'user': request.user})

# Kullanıcı kayıt olma
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Kullanıcıyı kaydettikten sonra giriş yap
            return redirect('question_list')  # Giriş yaptıktan sonra ana sayfaya yönlendir
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

# Özel giriş formu
class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'core/login.html'

def question_map(request):
    questions = Question.objects.all()  # Tüm soruları alıyoruz
    return render(request, 'core/question_map.html', {'questions': questions})

