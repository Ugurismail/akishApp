from django import forms
from django.contrib.auth.models import User
from .models import Question, Answer, StartingQuestion
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Message
from .models import Invitation



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

class SignupForm(UserCreationForm):
    username = forms.CharField(label='Kullanıcı Adı', max_length=30)
    password1 = forms.CharField(label='Şifre', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Şifre Tekrar', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

        self.fields['username'].error_messages = {'required': 'Kullanıcı adı gereklidir.'}
        self.fields['password1'].error_messages = {'required': 'Şifre gereklidir.'}
        self.fields['password2'].error_messages = {'required': 'Şifre tekrar gereklidir.'}

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Şifreler eşleşmiyor.")
        return password2

class WordUsageForm(forms.Form):
    word = forms.CharField(label='Kelime', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aramak istediğiniz kelime'}))

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Alıcı'
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Konu'
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        label='Mesaj'
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']

class SignupForm(UserCreationForm):
    username = forms.CharField(label='Kullanıcı Adı', max_length=30)
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(label='Şifre', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Şifre Tekrar', widget=forms.PasswordInput)
    invitation_code = forms.UUIDField(label='Davet Kodu')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'invitation_code')

    def clean_invitation_code(self):
        code = self.cleaned_data.get('invitation_code')
        try:
            invitation = Invitation.objects.get(code=code, is_accepted=False)
        except Invitation.DoesNotExist:
            raise forms.ValidationError("Geçersiz veya kullanılmış davet kodu.")
        return code


class InvitationForm(forms.ModelForm):
    recipient_email = forms.EmailField(label='Alıcının E-postası')
    quota_granted = forms.IntegerField(label='Davet Hakkı Sayısı', min_value=1)

    class Meta:
        model = Invitation
        fields = ['recipient_email', 'quota_granted']

    def __init__(self, *args, **kwargs):
        self.user_quota = kwargs.pop('user_quota')
        super().__init__(*args, **kwargs)

    def clean_quota_granted(self):
        quota = self.cleaned_data.get('quota_granted')
        if self.user_quota != float('inf') and quota > self.user_quota:
            raise forms.ValidationError(f"En fazla {self.user_quota} davet hakkı verebilirsiniz.")
        return quota


class GrantQuotaForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label='Kullanıcı')
    quota = forms.IntegerField(label='Davet Hakkı Sayısı', min_value=1)
