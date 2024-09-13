# forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Question, Answer, StartingQuestion
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm



class StartingQuestionForm(forms.ModelForm):
    # Aynı anda hem soru hem de cevap eklemek için alanlar
    answer_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya yazın'}))

    class Meta:
        model = Question
        fields = ['question_text']  # Yalnızca soru başlığı ekleniyor
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soru başlığı'}),
        }

    def __init__(self, *args, **kwargs):
        super(StartingQuestionForm, self).__init__(*args, **kwargs)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'password']

class QuestionForm(forms.ModelForm):
    answer_text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya yazın'}),
        required=False
    )

    class Meta:
        model = Question
        fields = ['question_text', 'answer_text']
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soru metni girin'}),
        }

    def __init__(self, *args, **kwargs):
        exclude_parent_questions = kwargs.pop('exclude_parent_questions', False)
        super(QuestionForm, self).__init__(*args, **kwargs)
        if exclude_parent_questions:
            self.fields.pop('parent_questions', None)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        widgets = {
            'answer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya girin'}),
        }

    def __init__(self, *args, **kwargs):
        super(AnswerForm, self).__init__(*args, **kwargs)
        self.fields['answer_text'].widget.attrs.update({'class': 'form-control'})

# Diğer form sınıfları değişmeden kalabilir
