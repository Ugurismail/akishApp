from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Question, Answer, StartingQuestion
from .forms import QuestionForm, AnswerForm, StartingQuestionForm, SignupForm, LoginForm
import json
from django.db.models import Q
from django.http import JsonResponse
import colorsys

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Otomatik giriş yapmak isterseniz
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
    answers = question.answers.all().order_by('created_at')  # Yanıtları kronolojik sırayla al

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
            question_text = form.cleaned_data['question_text']
            # Aynı soru metni varsa mevcut olanı kullan
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            if created:
                question.user = request.user
                question.save()
                form.save_m2m()  # ManyToMany ilişkileri kaydetmek için
            return redirect('question_list')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})

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

def get_user_color(user_id):
    # Kullanıcı ID'sine göre renk üret
    hue = (user_id * 137.508) % 360  # Altın açı
    rgb = colorsys.hsv_to_rgb(hue / 360, 0.5, 0.95)
    hex_color = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    return hex_color
def question_map(request):
    # Tüm soruları ve alt soruları getir
    questions = Question.objects.all()

    # Kullanıcı renkleri için bir sözlük
    user_colors = {}
    color_palette = ['#FF5733', '#33FF57', '#3357FF', '#F333FF', '#33FFF3', '#F3FF33']  # Örnek renkler
    color_index = 0

    # Tüm kullanıcıları al ve renkleri ata
    users = User.objects.all()
    for user in users:
        user_colors[user.id] = color_palette[color_index % len(color_palette)]
        color_index += 1

    # Düğümler (Nodes) oluşturma
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
                "size": 20 + 5 * (len(user_ids) - 1),  # Kullanıcı sayısına göre boyut
                "color": ''
            }
            if len(user_ids) == 1:
                node["color"] = user_colors[user_ids[0]]
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'  # Ortak sorular için gri renk
            else:
                node["color"] = '#000000'  # Hiçbir kullanıcıya ait değilse siyah
            nodes.append(node)
            node_ids.add(question.id)

    # Bağlantılar (Links) oluşturma
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

    # JSON verisi olarak frontend'e gönder
    return render(request, 'core/question_map.html', {'question_nodes': json.dumps(question_nodes)})

# Kullanıcının başlangıç sorularını listeleyen ana sayfa
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

            # Soru mevcutsa getir, yoksa oluştur
            subquestion, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            # Kullanıcıyı 'users' alanına ekle
            subquestion.users.add(request.user)
            subquestion.save()

            # Alt soru ilişkisini ekle
            parent_question.subquestions.add(subquestion)
            parent_question.save()

            # Yanıtı kaydet
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

            # Soru mevcutsa getir, yoksa oluştur
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            # Kullanıcıyı 'users' alanına ekle
            question.users.add(request.user)
            question.save()

            # Başlangıç sorusu olarak ekle
            StartingQuestion.objects.create(user=request.user, question=question)

            # Yanıtı kaydet
            Answer.objects.create(
                question=question,
                user=request.user,
                answer_text=form.cleaned_data['answer_text']
            )

            return redirect('user_homepage')
    else:
        form = StartingQuestionForm()
    
    return render(request, 'core/add_starting_question.html', {'form': form})


  # Import Q for complex queries

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

    # Düğümler ve bağlantıları oluşturma (mevcut question_map fonksiyonundaki gibi)
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

    # Bağlantılar
    links = []
    for question in questions:
        for subquestion in question.subquestions.all():
            if subquestion in questions:
                links.append({
                    "source": f"q{question.id}",
                    "target": f"q{subquestion.id}"
                })

    return JsonResponse({'nodes': nodes, 'links': links})
