# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Review, CustomUser, Booking, Service, Equipment, Role
from datetime import timedelta
from django.utils import timezone


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['user', 'service', 'equipment', 'start_date', 'duration_type']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control with-icon'}),
            'service': forms.Select(attrs={'class': 'form-control with-icon'}),
            'equipment': forms.Select(attrs={'class': 'form-control with-icon'}),
            'duration_type': forms.Select(attrs={'class': 'form-control with-icon'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].widget = forms.HiddenInput()
        self.fields['user'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        duration_type = cleaned_data.get('duration_type')
        service = cleaned_data.get('service')

        if not service:
            raise ValidationError("Услуга обязательна для выбора.")

        if start_date and duration_type:
            if start_date < timezone.now():
                raise ValidationError("Дата начала не может быть в прошлом.")

            end_date = start_date + timedelta(hours=1) if duration_type == 'hour' else start_date + timedelta(days=1)
            cleaned_data['end_date'] = end_date

        return cleaned_data


# Форма для фильтрации бронирований
class BookingFilterForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        required=False,
        label='Услуга',
        empty_label='Все услуги'
    )
    equipment = forms.ModelChoiceField(
        queryset=Equipment.objects.all(),
        required=False,
        label='Оборудование',
        empty_label='Все оборудование'
    )
    start_date = forms.DateField(
        required=False,
        label='С даты',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        label='По дату',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    duration_type = forms.ChoiceField(
        choices=[('', 'Все'), ('hour', 'Час'), ('day', 'День')],
        required=False,
        label='Тип длительности'
    )


# Форма для аутентификации пользователя
class CustomAuthenticationForm(forms.Form):
    phone_number = forms.CharField(
        label='Номер телефона',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=12,
        help_text="Формат: +79991234567",
        label="Мобильный телефон"
    )
    first_name = forms.CharField(
        label="Ваше имя",
        required=False  # Делаем поле необязательным
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'phone_number', 'role', 'password1', 'password2']
        labels = {
            'first_name': "Ваше имя",
            'password1': "Пароль",
            'password2': "Подтверждение пароля",
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Удаляем все нецифры и проверяем формат
        cleaned_phone = ''.join(filter(str.isdigit, phone_number))
        if len(cleaned_phone) != 11:
            raise forms.ValidationError("Номер должен содержать ровно 11 цифр (включая код страны).")
        if not phone_number.startswith('+'):
            raise forms.ValidationError("Номер должен начинаться с '+'.")
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Пользователь с таким номером телефона уже существует.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and len(password1) < 8:
            raise forms.ValidationError("Пароль должен содержать минимум 8 символов.")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned_data


# Форма для заполнения отзыва
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок отзыва',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите ваш отзыв',
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите оценку',
            }),
        }
        labels = {
            'title': 'Заголовок отзыва',
            'content': 'Текст отзыва',
            'rating': 'Оценка',
        }
