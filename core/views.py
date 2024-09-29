from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Question, Answer, StartingQuestion, SavedItem, Vote
from .forms import QuestionForm, AnswerForm, StartingQuestionForm, SignupForm, LoginForm, WordUsageForm,InvitationForm
from django.http import JsonResponse
from django.db.models import Q,Count
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
from .models import Message
from .forms import MessageForm
from .models import Invitation, UserProfile
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from collections import Counter
import colorsys, re, json


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data['email']
                user.save()
                # Kullanıcının profilini oluştur
                UserProfile.objects.get_or_create(user=user)
                # Davetiyeyi işle
                code = form.cleaned_data['invitation_code']
                try:
                    invitation = Invitation.objects.get(code=code, is_accepted=False)
                    invitation.is_accepted = True
                    invitation.accepted_by = user
                    invitation.accepted_at = timezone.now()
                    invitation.save()
                    # Davet hakkını kullanıcıya ekle
                    profile = user.userprofile
                    profile.invitation_quota += invitation.quota_granted
                    profile.save()
                except Invitation.DoesNotExist:
                    pass
                login(request, user)
            return redirect('user_homepage')
    else:
        invitation_code = request.GET.get('invitation_code', None)
        form = SignupForm(initial={'invitation_code': invitation_code})
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
    # Soru ve ilgili verileri al
    question = get_object_or_404(Question, id=question_id)
    answers = Answer.objects.filter(question=question).order_by('created_at')
    subquestions = question.subquestions.all()

    # Kullanıcı soruyu kaydetmiş mi?
    user_has_saved_question = SavedItem.objects.filter(user=request.user, question=question).exists()

    # Soru için kaydedilme sayısı
    question_save_count = SavedItem.objects.filter(question=question).count()

    # Yanıtlar için kaydedilme sayıları
    answer_save_counts = SavedItem.objects.filter(answer__in=answers).values('answer_id').annotate(count=Count('id'))
    answer_save_dict = {item['answer_id']: item['count'] for item in answer_save_counts}

    # Kullanıcının kaydettiği yanıtların ID'lerini al
    saved_answer_ids = SavedItem.objects.filter(user=request.user, answer__in=answers).values_list('answer__id', flat=True)

    # Yanıt ekleme formu
    form = AnswerForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            answer = form.save(commit=False)
            answer.user = request.user
            answer.question = question
            answer.save()
            messages.success(request, 'Yanıtınız başarıyla eklendi.')
            return redirect('question_detail', question_id=question.id)

    context = {
        'question': question,
        'answers': answers,
        'subquestions': subquestions,
        'form': form,
        'user_has_saved_question': user_has_saved_question,
        'saved_answer_ids': saved_answer_ids,
        'answer_save_dict': answer_save_dict,
        'question_save_count': question_save_count,
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
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yanıt başarıyla güncellendi.')
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
    nodes = {}
    links = []
    question_text_to_ids = defaultdict(list)

    # Build nodes dictionary keyed by question_text
    for question in questions:
        key = question.question_text
        question_text_to_ids[key].append(question.id)
        if key not in nodes:
            associated_users = list(question.users.all())
            user_ids = [user.id for user in associated_users]
            node = {
                "id": f"q{hash(key)}",  # Unique ID based on question_text
                "label": question.question_text,
                "users": user_ids,
                "size": 20 + 10 * (len(user_ids) - 1),
                "color": '',
                "question_id": question.id,  # Store a valid question ID
                "question_ids": [question.id],  # List of question IDs with same text
            }
            # Assign color based on user IDs
            if len(user_ids) == 1:
                node["color"] = get_user_color(user_ids[0])
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'  # Grey for multiple users
            else:
                node["color"] = '#000000'  # Black if no user
            nodes[key] = node
        else:
            # Merge user IDs and update size
            existing_node = nodes[key]
            new_user_ids = [user.id for user in question.users.all()]
            combined_user_ids = list(set(existing_node["users"] + new_user_ids))
            existing_node["users"] = combined_user_ids
            existing_node["size"] = 20 + 5 * (len(combined_user_ids) - 1)
            existing_node["question_ids"].append(question.id)
            # Update color
            if len(combined_user_ids) == 1:
                existing_node["color"] = get_user_color(combined_user_ids[0])
            elif len(combined_user_ids) > 1:
                existing_node["color"] = '#CCCCCC'
            else:
                existing_node["color"] = '#000000'

    # Build links using question_text as keys
    link_set = set()
    for question in questions:
        source_key = question.question_text
        for subquestion in question.subquestions.all():
            target_key = subquestion.question_text
            if target_key in nodes:
                link_id = (nodes[source_key]["id"], nodes[target_key]["id"])
                if link_id not in link_set:
                    links.append({
                        "source": nodes[source_key]["id"],
                        "target": nodes[target_key]["id"]
                    })
                    link_set.add(link_id)

    question_nodes = {
        "nodes": list(nodes.values()),
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
            subquestion_text = form.cleaned_data['question_text']
            answer_text = form.cleaned_data.get('answer_text', '')
            # Yeni veya mevcut alt soruyu oluştururken 'user' bilgisini ekliyoruz
            subquestion, created = Question.objects.get_or_create(
                question_text=subquestion_text,
                defaults={'user': request.user}
            )
            subquestion.users.add(request.user)
            parent_question.subquestions.add(subquestion)
            # Yanıtı kaydet
            Answer.objects.create(
                question=subquestion,
                user=request.user,
                answer_text=answer_text
            )
            messages.success(request, 'Alt soru başarıyla eklendi.')
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
        user = current_user
    elif user_id:
        user = User.objects.get(id=user_id)
    else:
        user = None

    if user:
        # Retrieve all questions where the user is the creator or associated
        questions = Question.objects.filter(
            Q(user=user) | Q(users=user) | Q(subquestions__user=user)
        ).distinct()
    else:
        questions = Question.objects.all()

    nodes = {}
    links = []
    question_text_to_ids = defaultdict(list)

    # Node creation and merging logic (same as previously provided)
    for question in questions:
        key = question.question_text
        question_text_to_ids[key].append(question.id)
        if key not in nodes:
            associated_users = list(question.users.all())
            user_ids = [user.id for user in associated_users]
            node = {
                "id": f"q{hash(key)}",
                "label": question.question_text,
                "users": user_ids,
                "size": 20 + 5 * (len(user_ids) - 1),
                "color": '',
                "question_id": question.id,
                "question_ids": [question.id],
            }
            if len(user_ids) == 1:
                node["color"] = get_user_color(user_ids[0])
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'
            else:
                node["color"] = '#000000'
            nodes[key] = node
        else:
            existing_node = nodes[key]
            new_user_ids = [user.id for user in question.users.all()]
            combined_user_ids = list(set(existing_node["users"] + new_user_ids))
            existing_node["users"] = combined_user_ids
            existing_node["size"] = 20 + 5 * (len(combined_user_ids) - 1)
            existing_node["question_ids"].append(question.id)
            if len(combined_user_ids) == 1:
                existing_node["color"] = get_user_color(combined_user_ids[0])
            elif len(combined_user_ids) > 1:
                existing_node["color"] = '#CCCCCC'
            else:
                existing_node["color"] = '#000000'

    # Build links
    link_set = set()
    for question in questions:
        source_key = question.question_text
        for subquestion in question.subquestions.all():
            target_key = subquestion.question_text
            if target_key in nodes:
                link_id = (nodes[source_key]["id"], nodes[target_key]["id"])
                if link_id not in link_set:
                    links.append({
                        "source": nodes[source_key]["id"],
                        "target": nodes[target_key]["id"]
                    })
                    link_set.add(link_id)

    return JsonResponse({'nodes': list(nodes.values()), 'links': links})

def delete_question_and_subquestions(question):
    subquestions = question.subquestions.all()
    for sub in subquestions:
        delete_question_and_subquestions(sub)
    question.delete()

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == 'POST':
        if request.user == question.user:
            with transaction.atomic():
                # Delete all answers associated with the question by the user
                Answer.objects.filter(question=question, user=request.user).delete()
                # Remove the user from the question's users
                question.users.remove(request.user)
                if question.users.count() == 0:
                    # If no users are associated, delete the question and its subquestions
                    delete_question_and_subquestions(question)
                    messages.success(request, 'Soru ve alt soruları başarıyla silindi.')
                else:
                    messages.success(request, 'Soru sizin için silindi.')
            return redirect('user_homepage')
        else:
            messages.error(request, 'Bu soruyu silme yetkiniz yok.')
            return redirect('question_detail', question_id=question.id)
    else:
        return render(request, 'core/confirm_delete_question.html', {'question': question})

@login_required
def vote(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = int(request.POST.get('object_id'))
        value = int(request.POST.get('value'))  # 1 veya -1

        if content_type == 'question':
            question = get_object_or_404(Question, id=object_id)
            with transaction.atomic():
                vote, created = Vote.objects.get_or_create(
                    user=request.user,
                    question=question,
                    defaults={'value': value}
                )
                if not created:
                    # Kullanıcı daha önce oy vermiş
                    if vote.value != value:
                        # Önceki oyu geri al
                        if vote.value == 1:
                            question.upvotes -= 1
                        elif vote.value == -1:
                            question.downvotes -= 1
                        # Yeni oyu ekle
                        vote.value = value
                        vote.save()
                        if value == 1:
                            question.upvotes += 1
                        elif value == -1:
                            question.downvotes += 1
                    else:
                        # Aynı oya tekrar basıldıysa, oy geri çekilir
                        if vote.value == 1:
                            question.upvotes -= 1
                        elif vote.value == -1:
                            question.downvotes -= 1
                        vote.delete()
                else:
                    # Yeni oy
                    if value == 1:
                        question.upvotes += 1
                    elif value == -1:
                        question.downvotes += 1
                question.save()
            return JsonResponse({'upvotes': question.upvotes, 'downvotes': question.downvotes})
        elif content_type == 'answer':
            answer = get_object_or_404(Answer, id=object_id)
            with transaction.atomic():
                vote, created = Vote.objects.get_or_create(
                    user=request.user,
                    answer=answer,
                    defaults={'value': value}
                )
                if not created:
                    if vote.value != value:
                        if vote.value == 1:
                            answer.upvotes -= 1
                        elif vote.value == -1:
                            answer.downvotes -= 1
                        vote.value = value
                        vote.save()
                        if value == 1:
                            answer.upvotes += 1
                        elif value == -1:
                            answer.downvotes += 1
                    else:
                        if vote.value == 1:
                            answer.upvotes -= 1
                        elif vote.value == -1:
                            answer.downvotes -= 1
                        vote.delete()
                else:
                    if value == 1:
                        answer.upvotes += 1
                    elif value == -1:
                        answer.downvotes += 1
                answer.save()
            return JsonResponse({'upvotes': answer.upvotes, 'downvotes': answer.downvotes})
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
def user_homepage(request):
    starting_questions = StartingQuestion.objects.filter(user=request.user)
    today = timezone.now().date()
    todays_questions = Question.objects.filter(created_at__date=today)
    return render(request, 'core/user_homepage.html', {
        'starting_questions': starting_questions,
        'todays_questions': todays_questions,
    })

def about(request):
    return render(request, 'core/about.html')

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

def site_statistics(request):
    # Mevcut istatistikler
    user_count = User.objects.filter(
        Q(questions__isnull=False) | Q(answers__isnull=False)
    ).distinct().count()
    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()
    total_likes = Vote.objects.filter(value=1).count()
    total_dislikes = Vote.objects.filter(value=-1).count()

    # En çok soru soran kullanıcılar
    top_question_users = User.objects.annotate(
        question_count=Count('questions')
    ).order_by('-question_count')[:5]

    # En çok yanıt veren kullanıcılar
    top_answer_users = User.objects.annotate(
        answer_count=Count('answers')
    ).order_by('-answer_count')[:5]

    # En çok beğenilen sorular
    top_liked_questions = Question.objects.annotate(
        like_count=Count('vote', filter=Q(vote__value=1))
    ).order_by('-like_count')[:5]

    # En çok beğenilen yanıtlar
    top_liked_answers = Answer.objects.annotate(
        like_count=Count('vote', filter=Q(vote__value=1))
    ).order_by('-like_count')[:5]

    # En çok kaydedilen sorular
    top_saved_questions = Question.objects.annotate(
        save_count=Count('saveditem')
    ).order_by('-save_count')[:5]

    # En çok kaydedilen yanıtlar
    top_saved_answers = Answer.objects.annotate(
        save_count=Count('saveditem')
    ).order_by('-save_count')[:5]

    # Tüm soru ve yanıt metinlerini al
    question_texts = Question.objects.values_list('question_text', flat=True)
    answer_texts = Answer.objects.values_list('answer_text', flat=True)

    # Metinleri birleştir
    all_texts = ' '.join(question_texts) + ' ' + ' '.join(answer_texts)

    # Metinleri küçük harfe çevir ve özel karakterleri kaldır
    all_texts = all_texts.lower()
    words = re.findall(r'\b\w+\b', all_texts)

    # İstenmeyen kelimeleri çıkar (örn. bağlaçlar)
    stopwords = set([
        've', 'ile', 'bir', 'bu', 'için', 'da', 'de', 'ki', 'mi', 'ne', 'ama',
        'fakat', 'daha', 'çok', 'gibi', 'den', 'ben', 'sen', 'o', 'biz', 'siz',
        'onlar', 'mı', 'mu', 'mü', 'her', 'şey', 'sadece', 'bütün', 'diğer',
        'hem', 'veya', 'ya', 'şu', 'öyle', 'böyle', 'eğer', 'çünkü', 'kadar'
    ])
    filtered_words = [word for word in words if word not in stopwords]

    # Kelime sıklıklarını hesapla
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(10)

    # Kelime arama
    search_word = request.GET.get('search_word')
    search_word_count = None
    if search_word:
        search_word_count = word_counts.get(search_word.lower(), 0)

    context = {
        'user_count': user_count,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'total_likes': total_likes,
        'total_dislikes': total_dislikes,
        'top_question_users': top_question_users,
        'top_answer_users': top_answer_users,
        'top_liked_questions': top_liked_questions,
        'top_liked_answers': top_liked_answers,
        'top_saved_questions': top_saved_questions,
        'top_saved_answers': top_saved_answers,
        'top_words': top_words,
        'search_word_count': search_word_count,
        'search_word': search_word,
    }

    return render(request, 'core/site_statistics.html', context)

@login_required
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    if request.method == 'POST':
        answer.delete()
        messages.success(request, 'Yanıt başarıyla silindi.')
        return redirect('question_detail', question_id=answer.question.id)
    return render(request, 'core/delete_answer.html', {'answer': answer})

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, user=request.user)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Soru başarıyla silindi.')
        return redirect('user_homepage')
    return render(request, 'core/delete_question.html', {'question': question})

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    questions = Question.objects.filter(user=user)
    answers = Answer.objects.filter(user=user)
    return render(request, 'core/user_profile.html', {'profile_user': user, 'questions': questions, 'answers': answers})

@login_required
def inbox(request):
    messages = Message.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'core/inbox.html', {'messages': messages})

@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'core/sent_messages.html', {'messages': messages})

@login_required
def compose_message(request, username=None):
    if username:
        recipient = get_object_or_404(User, username=username)
    else:
        recipient = None

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox')
    else:
        form = MessageForm(initial={'recipient': recipient})

    return render(request, 'core/compose_message.html', {'form': form})

@login_required
def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.recipient != request.user and message.sender != request.user:
        return redirect('inbox')
    if message.recipient == request.user:
        message.is_read = True
        message.save()
    return render(request, 'core/view_message.html', {'message': message})

@login_required
def get_unread_message_count(request):
    count = Message.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})

@login_required
def send_invitation(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = InvitationForm(request.POST, user_quota=user_profile.invitation_quota)
        if form.is_valid():
            with transaction.atomic():
                invitation = form.save(commit=False)
                invitation.sender = request.user
                invitation.save()
                # Kullanıcının davet hakkını düşür
                user_profile.invitation_quota -= invitation.quota_granted
                user_profile.save()
                # Davetiyeyi e-posta ile gönder
                send_invitation_email(invitation)
            messages.success(request, 'Davet gönderildi.')
            return redirect('profile')
    else:
        form = InvitationForm(user_quota=user_profile.invitation_quota)
    return render(request, 'core/send_invitation.html', {'form': form})

def send_invitation_email(invitation):
    subject = 'Sitemize Davetlisiniz!'
    message = f"""Merhaba,

{invitation.sender.username} sizi sitemize davet etti!

Davet kodunuz: {invitation.code}

Kayıt olmak için şu linki kullanabilirsiniz:
http://your-domain.com/signup/?invitation_code={invitation.code}

İyi günler!"""
    recipient_list = [invitation.recipient_email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

@staff_member_required
def grant_invitation_quota(request):
    if request.method == 'POST':
        form = GrantQuotaForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            quota = form.cleaned_data['quota']
            profile = user.userprofile
            profile.invitation_quota += quota
            profile.save()
            messages.success(request, f"{user.username} kullanıcısına {quota} davet hakkı verildi.")
            return redirect('profile', username=user.username)
    else:
        form = GrantQuotaForm()
    return render(request, 'core/grant_invitation_quota.html', {'form': form})

def single_answer(request, question_id, answer_id):
    question = get_object_or_404(Question, id=question_id)
    answer = get_object_or_404(Answer, id=answer_id, question=question)
    show_all = request.GET.get('show_all')

    if show_all:
        answers = question.answers.all()
    else:
        answers = [answer]

    context = {
        'question': question,
        'answers': answers,
        'single_answer_view': True,
    }
    return render(request, 'core/single_answer.html', context)