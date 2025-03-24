# core/forms.py
from django import forms
from .models import Review
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser
from django import forms
from .models import Booking, EquipmentHourly, EquipmentDaily, Service

# форма для бронирования услуги
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('service', 'equipment_hourly', 'equipment_daily', 'start_date', 'end_date')
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        equipment_hourly = cleaned_data.get('equipment_hourly')
        equipment_daily = cleaned_data.get('equipment_daily')

        # Проверяем, что выбрано либо почасовое, либо посуточное снаряжение, но не оба
        if equipment_hourly and equipment_daily:
            raise forms.ValidationError("Выберите либо почасовое, либо посуточное снаряжение, но не оба.")
        if not equipment_hourly and not equipment_daily and not cleaned_data.get('service'):
            raise forms.ValidationError("Выберите хотя бы одну услугу или снаряжение.")
        return cleaned_data

# форма для создания пользователя
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'first_name', 'password1', 'password2')

 # форма для заполнения отзыва
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