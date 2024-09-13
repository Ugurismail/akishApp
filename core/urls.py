# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_homepage, name='user_homepage'),
    path('add-starting-question/', views.add_starting_question, name='add_starting_question'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('question/<int:question_id>/add-subquestion/', views.add_subquestion, name='add_subquestion'),
    path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('map/', views.question_map, name='question_map'),
    path('search/', views.search_questions, name='search_questions'),
    path('user-search/', views.user_search, name='user_search'),
    path('map-data/', views.map_data, name='map_data'),
]