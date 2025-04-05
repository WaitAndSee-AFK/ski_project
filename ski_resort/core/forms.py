# core/forms.py
from django import forms
from .models import Review, CustomUser, Booking, Service, Equipment
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class BookingFilterForm(forms.Form):
    STATUS_CHOICES = (('', 'Все'),) + Booking.STATUS_CHOICES
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label='Статус')
    start_date = forms.DateField(required=False, label='С даты', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, label='По дату', widget=forms.DateInput(attrs={'type': 'date'}))

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Номер телефона', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

# Форма для бронирования услуги
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('service', 'equipment', 'start_date', 'end_date', 'duration_type')
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration_type': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'equipment': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'service': 'Услуга',
            'equipment': 'Оборудование',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'duration_type': 'Тип длительности',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        equipment = cleaned_data.get('equipment')
        service = cleaned_data.get('service')
        duration_type = cleaned_data.get('duration_type')

        # Проверка, что дата окончания позже даты начала
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError("Дата окончания должна быть позже даты начала.")

        # Проверка, что выбрана услуга или оборудование
        if not service and not equipment:
            raise forms.ValidationError("Выберите хотя бы одну услугу или оборудование.")

        # Проверка, что если выбрано оборудование, то указан тип длительности
        if equipment and not duration_type:
            raise forms.ValidationError("Укажите тип длительности (час или день) для оборудования.")

        # Проверка доступности оборудования
        if equipment and equipment.status == 'repair':
            raise forms.ValidationError("Выбранное оборудование находится в ремонте.")

        return cleaned_data


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Минимум 8 символов',
            'minlength': '8'
        }),
        min_length=8,
        help_text='Минимум 8 символов'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'phone_number')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше настоящее имя',
                'required': 'required'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (___) ___-__-__',
                'pattern': '^\+7\s?[\(]?\d{3}[\)]?\s?\d{3}[\-]?\d{2}[\-]?\d{2}$',
                'title': 'Формат: +7 (XXX) XXX-XX-XX'
            }),
        }
        labels = {
            'first_name': 'Ваше имя',
            'phone_number': 'Мобильный телефон',
        }
        help_texts = {
            'phone_number': 'Формат: +7 (XXX) XXX-XX-XX',
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.startswith('+7'):
            raise ValidationError("Номер должен начинаться с +7")
        if len(phone_number) < 11:
            raise ValidationError("Номер слишком короткий")
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("Этот номер уже зарегистрирован")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Пароли не совпадают")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['phone_number']  # Используем телефон как логин
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

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