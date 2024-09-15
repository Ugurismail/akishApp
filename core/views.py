from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Question, Answer, StartingQuestion, SavedItem
from .forms import QuestionForm, AnswerForm, StartingQuestionForm, SignupForm, LoginForm, WordUsageForm
import json
from django.http import JsonResponse
from django.db.models import Q,Count
from django.contrib import messages
from django.db import transaction
import colorsys
import re



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
# views.py

@login_required
def profile(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user

    # Kullanıcının soruları ve yanıtlarını alıyoruz
    questions = profile_user.questions.all()
    answers = profile_user.answers.all()

    # Kaydedilen sorular ve yanıtlar (eğer profil giriş yapan kullanıcıya aitse)
    if profile_user == request.user:
        saved_questions = SavedItem.objects.filter(user=profile_user, question__isnull=False).select_related('question')
        saved_answers = SavedItem.objects.filter(user=profile_user, answer__isnull=False).select_related('answer')
    else:
        saved_questions = None
        saved_answers = None

    # En çok kullanılan kelimeler ve kelime arama fonksiyonu (sadece kendi profiliniz için)
    top_words = []
    word_usage_data = None
    exclude_words = ''
    search_word = ''
    if profile_user == request.user:
        exclude_words = request.GET.get('exclude_words', '')
        exclude_words_list = [word.strip().lower() for word in exclude_words.split(',')] if exclude_words else []

        # Kullanıcının tüm yanıt metinlerini ve soru başlıklarını birleştir
        all_text = ' '.join(answer.answer_text.lower() for answer in answers)
        all_text += ' ' + ' '.join(question.question_text.lower() for question in questions)

        # Kelimeleri say
        words = re.findall(r'\b\w+\b', all_text)
        word_counts = {}
        for word in words:
            word = word.strip('.,!?()[]{}"\'').lower()
            if word and word not in exclude_words_list:
                word_counts[word] = word_counts.get(word, 0) + 1

        # En çok kullanılan 10 kelime
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Kelime kullanım sayısı arama
        search_word = request.GET.get('search_word', '').lower().strip()
        if search_word:
            pattern = r'\b{}\b'.format(re.escape(search_word))
            question_count = sum(len(re.findall(pattern, q.question_text.lower())) for q in questions)
            answer_count = sum(len(re.findall(pattern, a.answer_text.lower())) for a in answers)
            total_count = question_count + answer_count
            word_usage_data = {
                'word': search_word,
                'question_count': question_count,
                'answer_count': answer_count,
                'total_count': total_count,
            }

    context = {
        'profile_user': profile_user,
        'questions': questions,
        'answers': answers,
        'saved_questions': saved_questions,
        'saved_answers': saved_answers,
        'top_words': top_words,
        'exclude_words': exclude_words,
        'search_word': search_word,
        'word_usage_data': word_usage_data,
    }
    return render(request, 'core/profile.html', context)

@login_required
def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = Answer.objects.filter(question=question)
    subquestions = question.subquestions.all()
    user_has_saved_question = SavedItem.objects.filter(user=request.user, question=question).exists()
    form = AnswerForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            answer = form.save(commit=False)
            answer.user = request.user
            answer.question = question
            answer.save()
            return redirect('question_detail', question_id=question.id)
    # Her bir yanıt için kullanıcının kaydedip kaydetmediğini kontrol edelim
    for answer in answers:
        answer.user_has_saved = SavedItem.objects.filter(user=request.user, answer=answer).exists()
    context = {
        'question': question,
        'answers': answers,
        'subquestions': subquestions,
        'form': form,
        'user_has_saved_question': user_has_saved_question,
    }
    return render(request, 'core/question_detail.html', context)



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
        form = QuestionForm(request.POST)
        if form.is_valid():
            subquestion = form.save(commit=False)
            subquestion.user = request.user
            subquestion.save()
            subquestion.parent_questions.add(parent_question)
            return redirect('question_detail', question_id=subquestion.id)
    else:
        form = QuestionForm()
    context = {
        'form': form,
        'parent_question': parent_question,
    }
    return render(request, 'core/add_subquestion.html', context)

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
    
@login_required
def vote(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')
        value = int(request.POST.get('value'))

        if content_type == 'question':
            question = Question.objects.get(id=object_id)
            vote, created = Vote.objects.get_or_create(user=request.user, question=question)
            question.votes -= vote.value  # Eski oyu çıkar
            vote.value = value
            vote.save()
            question.votes += value  # Yeni oyu ekle
            question.save()
            return JsonResponse({'votes': question.votes})
        elif content_type == 'answer':
            answer = Answer.objects.get(id=object_id)
            vote, created = Vote.objects.get_or_create(user=request.user, answer=answer)
            answer.votes -= vote.value  # Eski oyu çıkar
            vote.value = value
            vote.save()
            answer.votes += value  # Yeni oyu ekle
            answer.save()
            return JsonResponse({'votes': answer.votes})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def save_item(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')

        if content_type == 'question':
            question = Question.objects.get(id=object_id)
            saved_item, created = SavedItem.objects.get_or_create(user=request.user, question=question)
            if not created:
                saved_item.delete()  # Zaten kayıtlıysa kaldır
                return JsonResponse({'status': 'removed'})
            else:
                return JsonResponse({'status': 'saved'})
        elif content_type == 'answer':
            answer = Answer.objects.get(id=object_id)
            saved_item, created = SavedItem.objects.get_or_create(user=request.user, answer=answer)
            if not created:
                saved_item.delete()  # Zaten kayıtlıysa kaldır
                return JsonResponse({'status': 'removed'})
            else:
                return JsonResponse({'status': 'saved'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def search_questions(request):
    query = request.GET.get('q', '')
    ajax = request.GET.get('ajax', None)
    results = Question.objects.filter(question_text__icontains=query)

    if ajax:
        data = {
            'results': list(results.values('id', 'question_text'))
        }
        return JsonResponse(data)
    else:
        return render(request, 'core/search_results.html', {'results': results})
    

@login_required
def delete_saved_item(request, item_id):
    saved_item = get_object_or_404(SavedItem, id=item_id, user=request.user)
    if request.method == 'POST':
        saved_item.delete()
        return redirect('profile')
    return render(request, 'core/confirm_delete_saved_item.html', {'saved_item': saved_item})

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    # Kullanıcının profil bilgilerini ve içeriklerini alabilirsiniz
    context = {
        'profile_user': user,
    }
    return render(request, 'core/user_profile.html', context)