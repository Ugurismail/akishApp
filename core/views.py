# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Question, Answer, StartingQuestion
from .forms import QuestionForm, AnswerForm, StartingQuestionForm, SignupForm, LoginForm
import json
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.db import transaction
import colorsys

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('user_homepage')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('user_homepage')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'core/profile.html', {'user': request.user})

@login_required
def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.all().order_by('created_at')
    subquestions = question.get_subquestions()

    # Yanıt formu işlemleri
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.user = request.user
            answer.save()
            return redirect('question_detail', question_id=question.id)
    else:
        form = AnswerForm()

    return render(request, 'core/question_detail.html', {
        'question': question,
        'answers': answers,
        'subquestions': subquestions,
        'form': form
    })

@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question_text']
            # Aynı soru metni varsa mevcut olanı kullan
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            question.users.add(request.user)
            question.save()
            # Başlangıç sorusu olarak ekle
            StartingQuestion.objects.create(user=request.user, question=question)
            # Yanıtı kaydet
            Answer.objects.create(
                question=question,
                user=request.user,
                answer_text=form.cleaned_data.get('answer_text', '')
            )
            return redirect('user_homepage')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})

@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            return redirect('question_detail', question_id=answer.question.id)
    else:
        form = AnswerForm(instance=answer)
    return render(request, 'core/edit_answer.html', {'form': form, 'answer': answer})

def get_user_color(user_id):
    hue = (user_id * 137.508) % 360  # Altın açı
    rgb = colorsys.hsv_to_rgb(hue / 360, 0.5, 0.95)
    hex_color = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    return hex_color

@login_required
def question_map(request):
    questions = Question.objects.all()
    nodes = []
    node_ids = set()
    for question in questions:
        if question.id not in node_ids:
            associated_users = list(question.users.all())
            user_ids = [user.id for user in associated_users]
            node = {
                "id": f"q{question.id}",
                "label": question.question_text,
                "users": user_ids,
                "size": 20 + 5 * (len(user_ids) - 1),
                "color": ''
            }
            if len(user_ids) == 1:
                node["color"] = get_user_color(user_ids[0])
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'
            else:
                node["color"] = '#000000'
            nodes.append(node)
            node_ids.add(question.id)

    links = []
    for question in questions:
        for subquestion in question.subquestions.all():
            links.append({
                "source": f"q{question.id}",
                "target": f"q{subquestion.id}"
            })

    question_nodes = {
        "nodes": nodes,
        "links": links
    }
    return render(request, 'core/question_map.html', {'question_nodes': json.dumps(question_nodes)})

@login_required
def user_homepage(request):
    starting_questions = StartingQuestion.objects.filter(user=request.user)
    return render(request, 'core/user_homepage.html', {'starting_questions': starting_questions})

@login_required
def add_subquestion(request, question_id):
    parent_question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_form = AnswerForm(request.POST)
        if question_form.is_valid() and answer_form.is_valid():
            question_text = question_form.cleaned_data['question_text']
            subquestion, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            subquestion.users.add(request.user)
            subquestion.save()
            parent_question.subquestions.add(subquestion)
            parent_question.save()
            answer = answer_form.save(commit=False)
            answer.question = subquestion
            answer.user = request.user
            answer.save()
            return redirect('question_detail', question_id=parent_question.id)
    else:
        question_form = QuestionForm(exclude_parent_questions=True)
        answer_form = AnswerForm()
    return render(request, 'core/add_subquestion.html', {
        'parent_question': parent_question,
        'question_form': question_form,
        'answer_form': answer_form
    })

@login_required
def add_starting_question(request):
    if request.method == 'POST':
        form = StartingQuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question_text']
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            question.users.add(request.user)
            question.save()
            StartingQuestion.objects.create(user=request.user, question=question)
            Answer.objects.create(
                question=question,
                user=request.user,
                answer_text=form.cleaned_data['answer_text']
            )
            return redirect('user_homepage')
    else:
        form = StartingQuestionForm()
    return render(request, 'core/add_starting_question.html', {'form': form})

@login_required
def search_questions(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        questions = Question.objects.filter(question_text__icontains=query).values('id', 'question_text')[:10]
        results = list(questions)
    return JsonResponse({'results': results})

@login_required
def user_search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        users = User.objects.filter(username__icontains=query).values('id', 'username')[:10]
        results = list(users)
    return JsonResponse({'results': results})

@login_required
def map_data(request):
    filter_type = request.GET.get('filter', '')
    user_id = request.GET.get('user_id', '')
    current_user = request.user

    if filter_type == 'me':
        questions = Question.objects.filter(users=current_user)
    elif user_id:
        questions = Question.objects.filter(users__id=user_id)
    else:
        questions = Question.objects.all()

    nodes = []
    node_ids = set()
    for question in questions:
        if question.id not in node_ids:
            associated_users = list(question.users.all())
            user_ids = [user.id for user in associated_users]
            node = {
                "id": f"q{question.id}",
                "label": question.question_text,
                "users": user_ids,
                "size": 20 + 5 * (len(user_ids) - 1),
                "color": ''
            }
            if len(user_ids) == 1:
                node["color"] = get_user_color(user_ids[0])
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'
            else:
                node["color"] = '#000000'
            nodes.append(node)
            node_ids.add(question.id)

    links = []
    for question in questions:
        for subquestion in question.subquestions.all():
            if subquestion in questions:
                links.append({
                    "source": f"q{question.id}",
                    "target": f"q{subquestion.id}"
                })

    return JsonResponse({'nodes': nodes, 'links': links})

def delete_question_and_subquestions(question):
    subquestions = question.subquestions.all()
    for sub in subquestions:
        delete_question_and_subquestions(sub)
    question.delete()

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == 'POST':
        if request.user in question.users.all():
            with transaction.atomic():
                question.users.remove(request.user)
                question.save()
                Answer.objects.filter(question=question, user=request.user).delete()
                if question.users.count() == 0:
                    if question.subquestions.exists():
                        messages.warning(request, 'Bu soruyu silerseniz tüm alt soruları da silinecek.')
                    delete_question_and_subquestions(question)
                    messages.success(request, 'Soru ve alt soruları başarıyla silindi.')
                else:
                    messages.success(request, 'Soru sizin için silindi.')
        else:
            messages.error(request, 'Bu soruyu silme yetkiniz yok.')
        return redirect('user_homepage')
    else:
        return render(request, 'core/confirm_delete_question.html', {'question': question})
