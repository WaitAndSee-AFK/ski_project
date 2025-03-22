# core/forms.py
from django import forms
from .models import Review
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'first_name', 'password1', 'password2')

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок отзыва',  # Подсказка для поля "title"
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите ваш отзыв',       # Подсказка для поля "content"
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите оценку',          # Подсказка для поля "rating"
            }),
        }
        labels = {
            'title': 'Заголовок отзыва',
            'content': 'Текст отзыва',
            'rating': 'Оценка',
        }