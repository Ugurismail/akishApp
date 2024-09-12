from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from .models import Question, Answer, StartingQuestion
from .forms import QuestionForm, AnswerForm
import json
from .forms import StartingQuestionForm

# Kullanıcı Kayıt (Signup) View
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)  # Yeni kullanıcıyı giriş yap
            return redirect('question_list')
    else:
        form = UserCreationForm()

    return render(request, 'core/signup.html', {'form': form})

# Kullanıcı Giriş (Login) View
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('question_list')
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form})

# Kullanıcı Çıkış (Logout) View
def user_logout(request):
    logout(request)
    return redirect('login')

# Kullanıcı Profili View
@login_required
def profile(request):
    return render(request, 'core/profile.html', {'user': request.user})

@login_required
def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.all()  # Sorunun tüm cevapları

    # Ana sorunun alt sorularını alıyoruz
    subquestions = question.get_subquestions()

    return render(request, 'core/question_detail.html', {
        'question': question,
        'answers': answers,
        'subquestions': subquestions  # Alt sorular burada
    })

@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.save()
            form.save_m2m()  # ManyToMany ilişkileri kaydetmek için bu gerekli
            return redirect('question_list')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})

@login_required
@login_required
def add_subquestion(request, question_id):
    parent_question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_form = AnswerForm(request.POST)
        if question_form.is_valid() and answer_form.is_valid():
            # Create subquestion
            subquestion = question_form.save(commit=False)
            subquestion.user = request.user
            subquestion.save()

            # Link it to the parent question
            parent_question.subquestions.add(subquestion)
            parent_question.save()

            # Save the first answer for the subquestion
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

# Yanıt Düzenleme View
@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()  # Güncelleme yapılır ve updated_at otomatik olarak güncellenir.
            return redirect('question_detail', question_id=answer.question.id)
    else:
        form = AnswerForm(instance=answer)
    
    return render(request, 'core/edit_answer.html', {'form': form, 'answer': answer})
# Soru Haritası View (D3.js Görselleştirmesi)
def question_map(request):
    # Tüm soruları ve alt soruları getir
    questions = Question.objects.all()

    # Düğümler (Nodes) oluşturma
    nodes = [{"id": f"q{question.id}", "label": question.question_text, "group": 1} for question in questions]

    # Bağlantılar (Links) oluşturma
    links = []
    for question in questions:
        for subquestion in question.subquestions.all():  # Alt sorular
            links.append({
                "source": f"q{question.id}",
                "target": f"q{subquestion.id}"
            })

    question_nodes = {
        "nodes": nodes,
        "links": links
    }

    # JSON verisi olarak frontend'e gönder
    return render(request, 'core/question_map.html', {'question_nodes': json.dumps(question_nodes)})

# Kullanıcının başlangıç sorularını listeleyen ana sayfa
def user_homepage(request):
    starting_questions = StartingQuestion.objects.filter(user=request.user)
    return render(request, 'core/user_homepage.html', {'starting_questions': starting_questions})

def add_starting_question(request):
    if request.method == 'POST':
        form = StartingQuestionForm(request.POST)
        if form.is_valid():
            # İlk önce soruyu kaydediyoruz
            question = form.save(commit=False)
            question.user = request.user
            question.save()

            # Sonrasında bu soru için bir yanıt ekliyoruz
            Answer.objects.create(
                question=question,
                user=request.user,
                answer_text=form.cleaned_data['answer_text']
            )

            # Son olarak, bu soruyu kullanıcının başlangıç sorusu olarak kaydediyoruz
            StartingQuestion.objects.create(user=request.user, question=question)

            return redirect('user_homepage')  # Başarılı eklemeden sonra ana sayfaya yönlendir
    else:
        form = StartingQuestionForm()
    
    return render(request, 'core/add_starting_question.html', {'form': form})

