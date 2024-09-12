from django import forms
from django.contrib.auth.models import User
from .models import Question, Answer,StartingQuestion
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Kullanıcı Kayıt Formu
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


# Kullanıcı Giriş Formu (User authentication için gerekli)
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        fields = ['username', 'password']


# Soru Ekleme Formu (ManyToManyField için)
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'parent_questions']  # Alt sorular için çoklu seçim ekleniyor
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soru metni girin'}),
            'parent_questions': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})


# Yanıt Ekleme/Düzenleme Formu
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
