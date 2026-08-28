from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=False, label="ชื่อจริง")
    last_name = forms.CharField(max_length=50, required=False, label="นามสกุล")
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='student', label="บทบาท")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'role')