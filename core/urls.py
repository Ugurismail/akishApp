from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.user_homepage, name='user_homepage'),
    path('add-starting-question/', views.add_starting_question, name='add_starting_question'),
    path('signup/', views.signup, name='signup'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),  # Giriş yap
    path('logout/', LogoutView.as_view(), name='logout'),  # Çıkış yap
    path('profile/', views.profile, name='profile'),
    path('add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('question/<int:question_id>/add-subquestion/', views.add_subquestion, name='add_subquestion'),
    path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
    path('map/', views.question_map, name='question_map'),
]
