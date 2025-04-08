from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import Equipment, Service, Booking, Review, CustomUser
from .forms import ReviewForm, BookingForm, CustomUserCreationForm  # Импортируем форму из forms.py
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Equipment, Service, Booking, Review, CustomUser, Price, ServiceType
from .forms import ReviewForm, BookingForm, CustomUserCreationForm
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import login, authenticate
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return reverse_lazy('bookings_admin')  # Суперюзеры и сотрудники -> главная страница
        return reverse_lazy('profile')  # Обычные пользователи -> профиль

# Список услуг
def services_view(request):
    services = Service.objects.all()
    service_types = ServiceType.objects.all()  # Передаем все типы услуг для модальных окон
    bookings = Booking.objects.filter(user=request.user) if request.user.is_authenticated else None
    return render(request, 'services.html', {'services': services, 'service_types': service_types, 'bookings': bookings})

# Получение данных об услуге для редактирования
@login_required
def get_service(request, service_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    try:
        service = get_object_or_404(Service, id=service_id)
        price = service.price
        return JsonResponse({
            'success': True,
            'service': {
                'name': service.name,
                'service_type_id': service.service_type_id,  # Передаем ID типа услуги
                'description': service.description,
                'price_per_hour': str(price.price_per_hour) if price else '0.00',
                'price_per_day': str(price.price_per_day) if price else '0.00'
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Добавление новой услуги
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_service(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    try:
        name = request.POST.get('name')
        service_type_id = request.POST.get('service_type')
        description = request.POST.get('description')
        price_per_hour = request.POST.get('price_per_hour')
        price_per_day = request.POST.get('price_per_day')

        if not all([name, service_type_id, price_per_hour, price_per_day]):
            return JsonResponse({'success': False, 'error': 'Все поля обязательны'}, status=400)

        price = Price.objects.create(
            name=f"Цена для {name}",
            price_per_hour=price_per_hour,
            price_per_day=price_per_day
        )
        service = Service.objects.create(
            name=name,
            service_type_id=service_type_id,
            description=description,
            price=price
        )
        return JsonResponse({'success': True, 'id': service.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Редактирование услуги
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def edit_service(request, service_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    try:
        service = get_object_or_404(Service, id=service_id)
        name = request.POST.get('name')
        service_type_id = request.POST.get('service_type')
        description = request.POST.get('description')
        price_per_hour = request.POST.get('price_per_hour')
        price_per_day = request.POST.get('price_per_day')

        if not all([name, service_type_id, price_per_hour, price_per_day]):
            return JsonResponse({'success': False, 'error': 'Все поля обязательны'}, status=400)

        service.name = name
        service.service_type_id = service_type_id
        service.description = description
        if service.price:
            service.price.price_per_hour = price_per_hour
            service.price.price_per_day = price_per_day
            service.price.save()
        else:
            price = Price.objects.create(
                name=f"Цена для {name}",
                price_per_hour=price_per_hour,
                price_per_day=price_per_day
            )
            service.price = price
        service.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Удаление услуги
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def delete_service(request, service_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    try:
        service = get_object_or_404(Service, id=service_id)
        # Проверка на связанные бронирования
        if service.bookings.exists():
            return JsonResponse({'success': False, 'error': 'Нельзя удалить услугу с активными бронированиями'}, status=400)
        # Удаляем только саму услугу, не трогаем Price
        service.delete()
        return JsonResponse({'success': True})
    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Услуга не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Отмена бронирования
@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            booking.status = 'canceled'
            booking.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Недопустимый метод запроса'})

# Список одобренных отзывов
def review_list(request):
    reviews = Review.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'review_list.html', {'reviews': reviews})

# Создание нового отзыва
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

# Модерация отзывов
@login_required
def review_moderation(request):
    if request.user.is_staff:
        reviews = Review.objects.filter(approved=False)
        return render(request, 'review_moderation.html', {'reviews': reviews})
    messages.warning(request, 'У вас нет прав для доступа к этой странице.')
    return redirect('review_list')

# Главная страница
class HomeView(View):
    def get(self, request):
        complex_info = {
            'name': 'Горнолыжный курорт Алтай',
            'description': 'Лучший курорт в регионе с современным оборудованием и трассами',
            'location': 'Горы Алтая'
        }
        return render(request, 'home.html', {'complex_info': complex_info})

# Цены из таблицы почасовые и посуточные
class PricingView(View):
    def get(self, request):
        prices = Price.objects.all()
        services = Service.objects.all()
        equipment = Equipment.objects.all()
        context = {
            'prices': prices,
            'services': services,
            'equipment': equipment,
        }
        return render(request, 'pricing.html', context)

# Регистрация нового пользователя
class RegisterView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone_number = form.cleaned_data.get('phone_number')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=phone_number, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('profile')
            else:
                messages.error(request, 'Ошибка аутентификации после регистрации.')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
        return render(request, 'register.html', {'form': form})

# Профиль пользователя с активными бронированиями
class ProfileView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'profile.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            status='active'
        ).select_related('service', 'equipment')

# Создание бронирования услуги
@login_required
@csrf_exempt
def book_service(request, service_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service = get_object_or_404(Service, id=service_id)

            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            duration_type = data.get('duration_type', 'hour')

            # Проверка на пересекающиеся бронирования
            conflicting_bookings = Booking.objects.filter(
                service=service,
                status='active',
                start_date__lt=end_date,
                end_date__gt=start_date
            )
            if conflicting_bookings.exists():
                return JsonResponse({'success': False, 'error': 'Выбранное время уже занято'})

            booking = Booking.objects.create(
                user=request.user,
                service=service,
                start_date=start_date,
                end_date=end_date,
                duration_type=duration_type,
                status='active',
                total_cost=service.calculate_cost() if service.price else 0
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

# Создание бронирования через форму
class BookServiceView(LoginRequiredMixin, View):
    def get(self, request):
        form = BookingForm()
        return render(request, 'booking_form.html', {'form': form})

    def post(self, request, service_id=None, equipment_id=None):
        try:
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                service_id = data.get('service_id')
                equipment_id = data.get('equipment_id')
                start_date_str = data.get('start_date')
                end_date_str = data.get('end_date')
                duration_type = data.get('duration_type', 'hour')

                if not start_date_str or not end_date_str:
                    raise ValueError("Дата начала и окончания обязательны")

                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                form = BookingForm(request.POST)
                if form.is_valid():
                    booking = form.save(commit=False)
                    booking.user = request.user
                    booking.status = 'active'
                    booking.save()
                    messages.success(request, 'Бронирование успешно создано!')
                    return redirect('profile')
                else:
                    messages.error(request, 'Исправьте ошибки в форме.')
                    return render(request, 'booking_form.html', {'form': form})

            if service_id:
                item = get_object_or_404(Service, id=service_id)
                booking_type = 'service'
            elif equipment_id:
                item = get_object_or_404(Equipment, id=equipment_id)
                booking_type = 'equipment'
            else:
                raise ValueError("Не указан объект бронирования")

            conflicting_bookings = Booking.objects.filter(
                status='active',
                start_date__lt=end_date,
                end_date__gt=start_date
            ).filter(
                service=item if booking_type == 'service' else None,
                equipment=item if booking_type == 'equipment' else None
            )
            if conflicting_bookings.exists():
                raise ValueError("Выбранное время уже занято")

            booking = Booking.objects.create(
                user=request.user,
                service=item if booking_type == 'service' else None,
                equipment=item if booking_type == 'equipment' else None,
                start_date=start_date,
                end_date=end_date,
                duration_type=duration_type,
                status='active'
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

# Редактирование бронирования пользователем
@login_required
@require_http_methods(["POST"])
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

        conflicting_bookings = Booking.objects.filter(
            service=booking.service,
            status='active',
            start_date__lt=end_date,
            end_date__gt=start_date
        ).exclude(id=booking.id)
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

# Список всех бронирований для администратора
class AdminBookingsView(LoginRequiredMixin, ListView):
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

# Удалены неиспользуемые функции
# create_price, update_price, delete_price заменены на add_service, edit_service, delete_service

@csrf_exempt
@require_http_methods(["POST"])
def create_price(request):
    try:
        data = json.loads(request.body)
        price = Price.objects.create(
            name=data['name'],
            price_per_hour=data['price_per_hour'],
            price_per_day=data['price_per_day']
        )

        if data.get('service_id'):
            service = Service.objects.get(id=data['service_id'])
            service.price = price
            service.description = data.get('description', '')
            service.save()

        return JsonResponse({'success': True, 'id': price.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT"])
def update_price(request, pk):
    try:
        price = Price.objects.get(pk=pk)
        data = json.loads(request.body)

        price.name = data.get('name', price.name)
        price.price_per_hour = data.get('price_per_hour', price.price_per_hour)
        price.price_per_day = data.get('price_per_day', price.price_per_day)
        price.save()

        if data.get('service_id'):
            service = Service.objects.get(id=data['service_id'])
            service.description = data.get('description', '')
            service.save()

        return JsonResponse({'success': True})
    except Price.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Price not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def delete_price(request, pk):
    try:
        price = Price.objects.get(pk=pk)
        price.delete()
        return JsonResponse({'success': True})
    except Price.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Price not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

