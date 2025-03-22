# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Equipment, Service, Booking, Review, CustomUser
from .forms import ReviewForm
from datetime import datetime
import json

# Форма для регистрации
class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True, label='Номер телефона')
    first_name = forms.CharField(max_length=30, required=False, label='Имя')

    class Meta:
        model = CustomUser
        fields = ('phone_number', 'first_name', 'password1', 'password2')

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Этот номер телефона уже зарегистрирован.")
        return phone_number

@csrf_exempt
def cancel_booking(request, booking_id):
    """Отмена бронирования пользователем"""
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            booking.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Недопустимый метод запроса'})

def review_list(request):
    """Список утвержденных отзывов"""
    reviews = Review.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'review_list.html', {'reviews': reviews})

@login_required
def create_review(request):
    """Создание нового отзыва"""
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
    """Модерация отзывов (только для персонала)"""
    if request.user.is_staff:
        reviews = Review.objects.filter(approved=False)
        return render(request, 'review_moderation.html', {'reviews': reviews})
    messages.warning(request, 'У вас нет прав для доступа к этой странице.')
    return redirect('review_list')

class HomeView(View):
    """Главная страница"""
    def get(self, request):
        complex_info = {
            'name': 'Горнолыжный курорт Алтай',
            'description': 'Лучший курорт в регионе с современным оборудованием и трассами',
            'location': 'Горы Алтая'
        }
        context = {
            'complex_info': complex_info
        }
        return render(request, 'home.html', context)

class ServicesView(ListView):
    """Список услуг"""
    model = Service
    template_name = 'services.html'
    context_object_name = 'services'

class PricingView(ListView):
    """Список оборудования и цен"""
    model = Equipment
    template_name = 'pricing.html'
    context_object_name = 'equipment'

class RegisterView(View):
    """Регистрация нового пользователя"""
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone_number = form.cleaned_data.get('phone_number')
            user = authenticate(request, phone_number=phone_number, password=form.cleaned_data.get('password1'))
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
    """Профиль пользователя с активными бронированиями"""
    model = Booking
    template_name = 'profile.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('service', 'equipment')

class BookServiceView(LoginRequiredMixin, View):
    """Создание бронирования услуги или оборудования"""
    def post(self, request, service_id=None, equipment_id=None):
        try:
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                service_id = data.get('service_id')
                start_date_str = data.get('start_date')
                end_date_str = data.get('end_date')

                if not start_date_str or not end_date_str:
                    raise ValueError("Дата начала и окончания обязательны")

                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                service_id = service_id or request.POST.get('service_id')
                equipment_id = equipment_id or request.POST.get('equipment_id')
                start_date = request.POST.get('start_date') or timezone.now()
                end_date = request.POST.get('end_date') or (timezone.now() + timezone.timedelta(days=1))

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
                start_date=start_date,
                end_date=end_date
            )

            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True, 'message': 'Бронирование успешно создано'})
            messages.success(request, 'Бронирование успешно создано!')
        except ValueError as e:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            messages.error(request, f'Ошибка бронирования: {str(e)}')
        except Exception as e:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'Ошибка бронирования: {str(e)}')

        return redirect('profile')

@login_required
@require_POST
def edit_booking(request, booking_id):
    """Редактирование бронирования администратором"""
    if not request.user.is_staff:
        messages.warning(request, 'Доступ запрещен')
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id)
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')

    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Дата начала и окончания обязательны")
        booking.start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        booking.end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        booking.save()
        messages.success(request, 'Бронирование успешно обновлено')
    except ValueError as e:
        messages.error(request, f'Ошибка при обновлении: {str(e)}')
    except Exception as e:
        messages.error(request, f'Ошибка при обновлении: {str(e)}')

    return redirect('bookings_admin')

class AdminBookingsView(LoginRequiredMixin, ListView):
    """Список всех бронирований для администратора"""
    model = Booking
    template_name = 'admin_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.all().select_related('user', 'service', 'equipment')

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.warning(request, 'Доступ запрещен')
            return redirect('home')
        return super().get(request, *args, **kwargs)