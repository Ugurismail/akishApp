from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.question_list, name='question_list'),  # Ana sayfa - soru listesi
    path('add/', views.add_question, name='add_question'),  # Yeni soru ekleme
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),  # Soru detayları
    path('question/<int:question_id>/add_subquestion/', views.add_subquestion, name='add_subquestion'),  # Alt soru ekleme
    path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),  # Yanıt düzenleme
    path('signup/', views.signup, name='signup'),  # Kayıt olma
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Giriş yap
    path('logout/', auth_views.LogoutView.as_view(next_page='question_list'), name='logout'),  # Çıkış yap
    path('profile/', views.profile, name='profile'),  # Profil sayfası
    path('map/', views.question_map, name='question_map'),
]
