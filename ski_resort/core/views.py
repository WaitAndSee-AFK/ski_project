# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.models import User
from .models import Equipment, Service, Booking, Review, UserProfile  # Добавил UserProfile
from .forms import ReviewForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Booking

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Booking


@login_required
@require_POST
def edit_booking(request, booking_id):
    """Редактирование бронирования администратором"""
    if not request.user.is_staff:
        messages.warning(request, 'Доступ запрещен')
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id)
    booking.start_date = request.POST.get('start_date')
    booking.end_date = request.POST.get('end_date')

    try:
        booking.save()
        messages.success(request, 'Бронирование успешно обновлено')
    except Exception as e:
        messages.error(request, f'Ошибка при обновлении: {str(e)}')

    return redirect('bookings_admin')

class AdminBookingsView(LoginRequiredMixin, ListView):
    """Список всех бронирований для администратора"""
    model = Booking
    template_name = 'admin_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        # Показываем все бронирования, а не только активные
        return Booking.objects.all().select_related('user', 'service', 'equipment')

    def get(self, request, *args, **kwargs):
        # Проверяем, что пользователь является администратором
        if not request.user.is_staff:
            messages.warning(request, 'Доступ запрещен')
            return redirect('home')
        return super().get(request, *args, **kwargs)

@csrf_exempt
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            booking.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Недопустимый метод запроса'})


def review_list(request):
    reviews = Review.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'review_list.html', {'reviews': reviews})


@login_required
def create_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, 'Ваш отзыв успешно отправлен на модерацию.')
            return redirect('review_list')
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form})


@login_required
def review_moderation(request):
    if request.user.is_staff:
        reviews = Review.objects.filter(approved=False)
        return render(request, 'review_moderation.html', {'reviews': reviews})
    messages.warning(request, 'У вас нет прав для доступа к этой странице.')
    return redirect('review_list')


class HomeView(View):
    def get(self, request):
        complex_info = {
            'name': 'Горнолыжный курорт Алтай',
            'description': 'Лучший курорт в регионе с современным оборудованием и трассами',
            'location': 'Горы Алтая'
        }
        return render(request, 'home.html', {'complex_info': complex_info})


class ServicesView(ListView):
    model = Service
    template_name = 'services.html'
    context_object_name = 'services'


class PricingView(ListView):
    model = Equipment
    template_name = 'pricing.html'
    context_object_name = 'equipment'


# Добавил кастомную форму для регистрации
class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True, label='Номер телефона')

    class Meta:
        model = User
        fields = ('username', 'phone_number', 'password1', 'password2')


class RegisterView(View):
    def get(self, request):
        form = CustomUserCreationForm()  # Используем кастомную форму
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone_number = form.cleaned_data.get('phone_number')
            UserProfile.objects.create(user=user, phone_number=phone_number)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('profile')
            else:
                messages.error(request, 'Ошибка аутентификации.')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
        return render(request, 'register.html', {'form': form})


class ProfileView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'profile.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('service', 'equipment')


class BookServiceView(LoginRequiredMixin, View):
    def post(self, request, service_id=None, equipment_id=None):
        try:
            if service_id:
                item = get_object_or_404(Service, id=service_id)
                booking_type = 'service'
            elif equipment_id:
                item = get_object_or_404(Equipment, id=equipment_id)
                booking_type = 'equipment'
            else:
                raise ValueError("Не указан объект бронирования")

            Booking.objects.create(
                user=request.user,
                service=item if booking_type == 'service' else None,
                equipment=item if booking_type == 'equipment' else None,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=1))
            messages.success(request, 'Бронирование успешно создано!')
        except Exception as e:
            messages.error(request, f'Ошибка бронирования: {str(e)}')
        return redirect('profile')


# Форма для отзывов (осталась без изменений)
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