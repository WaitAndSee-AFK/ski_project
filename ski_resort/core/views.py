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
from .models import EquipmentHourly, EquipmentDaily, Service, Booking, Review, CustomUser
from .forms import ReviewForm, BookingForm
from datetime import datetime
import json


# форма для регистрации
class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True, label='Номер телефона')
    first_name = forms.CharField(max_length=30, required=False, label='Имя')

    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'first_name', 'password1', 'password2')

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Этот номер телефона уже зарегистрирован.")
        return phone_number


# отмена бронирования
@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            booking.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Недопустимый метод запроса'})


# список одобренных отзывов
def review_list(request):
    reviews = Review.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'review_list.html', {'reviews': reviews})


# создание нового отзыва
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


# модерация отзывов
@login_required
def review_moderation(request):
    if request.user.is_staff:
        reviews = Review.objects.filter(approved=False)
        return render(request, 'review_moderation.html', {'reviews': reviews})
    messages.warning(request, 'У вас нет прав для доступа к этой странице.')
    return redirect('review_list')

# главная страница
class HomeView(View):
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


# cписок услуг с бронированиями
class ServicesView(View):
    def get(self, request):
        services = Service.objects.all()
        bookings = Booking.objects.filter(user=request.user) if request.user.is_authenticated else None
        return render(request, 'services.html', {'services': services, 'bookings': bookings})


# цены из таблтцы почасовые и посуточные
class PricingView(View):
    def get(self, request):
        equipment_hourly = EquipmentHourly.objects.all()
        equipment_daily = EquipmentDaily.objects.all()
        context = {
            'equipment_hourly': equipment_hourly,
            'equipment_daily': equipment_daily,
        }
        return render(request, 'pricing.html', context)


# регистрация нового пользователя
class RegisterView(View):
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


# профиль пользователя с активными бронированиями
class ProfileView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'profile.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('service', 'equipment_hourly', 'equipment_daily')


# создание бронирования услуги
@csrf_exempt
@login_required
def book_service(request, service_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service = Service.objects.get(id=service_id)

            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '-03:00'))

            # проверка на существование пересекающихся бронирований
            conflicting_bookings = Booking.objects.filter(
                service=service,
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            )

            if conflicting_bookings.exists():
                return JsonResponse({'success': False, 'error': 'Выбранное время уже занято'})

            # создание нового бронирования
            booking = Booking.objects.create(
                user=request.user,
                service=service,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )

            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'message': 'Бронирование успешно создано'
            })
        except Service.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Услуга не найдена'})
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})


# создание бронирования через форму
class BookServiceView(LoginRequiredMixin, View):
    def get(self, request):
        form = BookingForm()
        return render(request, 'booking_form.html', {'form': form})

    def post(self, request, service_id=None, equipment_hourly_id=None, equipment_daily_id=None):
        try:
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                service_id = data.get('service_id')
                equipment_hourly_id = data.get('equipment_hourly_id')
                equipment_daily_id = data.get('equipment_daily_id')
                start_date_str = data.get('start_date')
                end_date_str = data.get('end_date')

                if not start_date_str or not end_date_str:
                    raise ValueError("Дата начала и окончания обязательны")

                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                form = BookingForm(request.POST)
                if form.is_valid():
                    booking = form.save(commit=False)
                    booking.user = request.user
                    booking.save()
                    messages.success(request, 'Бронирование успешно создано!')
                    return redirect('profile')
                else:
                    messages.error(request, 'Исправьте ошибки в форме.')
                    return render(request, 'booking_form.html', {'form': form})

            if service_id:
                item = get_object_or_404(Service, id=service_id)
                booking_type = 'service'
            elif equipment_hourly_id:
                item = get_object_or_404(EquipmentHourly, id=equipment_hourly_id)
                booking_type = 'equipment_hourly'
            elif equipment_daily_id:
                item = get_object_or_404(EquipmentDaily, id=equipment_daily_id)
                booking_type = 'equipment_daily'
            else:
                raise ValueError("Не указан объект бронирования")

            # Проверка пересечений для всех типов бронирований
            conflicting_bookings = Booking.objects.filter(
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).filter(
                service=item if booking_type == 'service' else None,
                equipment_hourly=item if booking_type == 'equipment_hourly' else None,
                equipment_daily=item if booking_type == 'equipment_daily' else None
            )

            if conflicting_bookings.exists():
                raise ValueError("Выбранное время уже занято")

            booking = Booking.objects.create(
                user=request.user,
                service=item if booking_type == 'service' else None,
                equipment_hourly=item if booking_type == 'equipment_hourly' else None,
                equipment_daily=item if booking_type == 'equipment_daily' else None,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )

            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'booking_id': booking.id,
                    'message': 'Бронирование успешно создано'
                })
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


# редактирование бронирования пользователем
@login_required
@require_POST
def edit_booking(request, booking_id):

    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        data = json.loads(request.body)
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not start_date_str or not end_date_str:
            return JsonResponse({'success': False, 'error': 'Дата начала и окончания обязательны'})

        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

        # проверка на пересекающиеся бронирования
        conflicting_bookings = Booking.objects.filter(
            service=booking.service,
            is_active=True,
            start_date__lt=end_date,
            end_date__gt=start_date
        ).exclude(id=booking.id)  # Исключаем текущее бронирование

        if conflicting_bookings.exists():
            return JsonResponse({'success': False, 'error': 'Выбранное время уже занято'})

        booking.start_date = start_date
        booking.end_date = end_date
        booking.save()

        return JsonResponse({'success': True, 'message': 'Бронирование успешно обновлено'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# список всех бронирований для администратора
class AdminBookingsView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'admin_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.all().select_related('user', 'service', 'equipment_hourly', 'equipment_daily')

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.warning(request, 'Доступ запрещен')
            return redirect('home')
        return super().get(request, *args, **kwargs)