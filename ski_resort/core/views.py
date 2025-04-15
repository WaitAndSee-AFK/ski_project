from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Equipment, Service, Booking, Review, CustomUser, Price, ServiceType, CustomUser
from .forms import ReviewForm, BookingForm, CustomUserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Booking, CustomUser, Service, Equipment
from .forms import BookingForm


def booking_list(request):
    # Убедимся, что данные загружаются правильно
    bookings = Booking.objects.all().select_related('user').prefetch_related('service', 'equipment')

    # Для отладки - проверим данные
    debug_info = []
    for booking in bookings:
        debug_info.append({
            'id': booking.id,
            'user': booking.user.id if booking.user else None,
            'phone': booking.user.phone_number if booking.user else None,
            'service': booking.service.name if booking.service else None
        })
    print("Debug booking info:", debug_info)  # Проверьте этот вывод в консоли сервера

    return render(request, 'admin_bookings.html', {
        'bookings': bookings,
    })


def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                booking = form.save()
                messages.success(request, 'Бронирование успешно создано.')
                return redirect('booking_list')
            except Exception as e:
                messages.error(request, f'Ошибка при создании бронирования: {str(e)}')
        else:
            # Выведем ошибки формы для отладки
            print("Form errors:", form.errors)
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = BookingForm()

    services = Service.objects.all()
    equipment = Equipment.objects.all()

    return render(request, 'create_booking.html', {
        'form': form,
        'users': CustomUser.objects.exclude(phone_number__isnull=True),
        'services': Service.objects.all(),
        'equipment': Equipment.objects.all(),
    })

def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно обновлено.')
            return redirect('booking_list')
        else:
            messages.error(request, 'Ошибка при обновлении бронирования.')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'edit_booking.html', {
        'form': form,
        'booking': booking,
        'users': CustomUser.objects.all(),
        'services': Service.objects.all(),
        'equipment': Equipment.objects.all(),  # Предполагается, что сервер фильтрует доступное оборудование
    })

def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Бронирование успешно удалено.')
        return redirect('booking_list')
    return redirect('booking_list')

logger = logging.getLogger(__name__)

@login_required
def bookings_view(request):
    logger.info(f"Запрос страницы бронирований от пользователя {request.user.phone_number}")
    if not (request.user.is_staff or request.user.is_superuser):
        logger.warning(f"Попытка доступа к странице бронирований без прав: {request.user.phone_number}")
        return HttpResponseForbidden("Доступ запрещён")

    bookings = Booking.objects.all().select_related('user', 'service', 'equipment').order_by('-start_date')
    users = CustomUser.objects.all()
    services = Service.objects.all()
    equipment = Equipment.objects.filter(status='ready')

    return render(request, 'admin_bookings.html', {
        'bookings': bookings,
        'users': users,
        'services': services,
        'equipment': equipment
    })

@login_required
@require_http_methods(["POST"])
def get_available_services(request):
    try:
        data = json.loads(request.body)
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        exclude_booking_id = data.get('exclude_booking_id')

        if not start_date_str or not end_date_str:
            return JsonResponse({'success': False, 'error': 'Не указаны даты'}, status=400)

        naive_start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
        naive_end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        start_date = timezone.make_aware(naive_start_date)
        end_date = timezone.make_aware(naive_end_date)

        conflicting_bookings = Booking.objects.filter(
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        if exclude_booking_id:
            conflicting_bookings = conflicting_bookings.exclude(id=exclude_booking_id)

        booked_service_ids = conflicting_bookings.exclude(service__isnull=True).values_list('service__id', flat=True)
        available_services = Service.objects.exclude(id__in=booked_service_ids)
        services_data = [
            {'id': s.id, 'name': s.name}
            for s in available_services
        ]

        return JsonResponse({
            'success': True,
            'services': services_data
        })
    except ValueError as e:
        logger.error(f"Ошибка формата даты: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Неверный формат даты'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при получении доступных услуг: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def get_available_equipment(request):
    try:
        data = json.loads(request.body)
        service_id = data.get('service_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        exclude_booking_id = data.get('exclude_booking_id')

        logger.info(f"Запрос оборудования: service_id={service_id}, start_date={start_date_str}, end_date={end_date_str}, exclude_booking_id={exclude_booking_id}")

        if not service_id or not start_date_str or not end_date_str:
            return JsonResponse({'success': False, 'error': 'Не указаны обязательные параметры'}, status=400)

        try:
            naive_start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            naive_end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError as e:
            logger.error(f"Неверный формат даты: {str(e)}. Попробуем другой формат.")
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError as e2:
                logger.error(f"Не удалось распарсить даты: {str(e2)}")
                return JsonResponse({'success': False, 'error': 'Неверный формат даты'}, status=400)
        else:
            start_date = timezone.make_aware(naive_start_date)
            end_date = timezone.make_aware(naive_end_date)

        equipment = Equipment.objects.filter(services__id=service_id, status='ready')
        logger.info(f"Найдено оборудования для услуги {service_id}: {list(equipment)}")

        available_equipment = []
        for equip in equipment:
            overlapping_bookings = Booking.objects.filter(
                equipment=equip,
                start_date__lt=end_date,
                end_date__gt=start_date
            )
            if exclude_booking_id:
                overlapping_bookings = overlapping_bookings.exclude(id=exclude_booking_id)

            logger.info(f"Оборудование {equip.name} (ID: {equip.id}): пересечения = {list(overlapping_bookings)}")

            if not overlapping_bookings.exists():
                available_equipment.append({
                    'id': equip.id,
                    'name': equip.name
                })

        logger.info(f"Доступное оборудование: {available_equipment}")
        return JsonResponse({'success': True, 'equipment': available_equipment})
    except ValueError as e:
        logger.error(f"Ошибка формата даты: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Неверный формат даты'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при получении оборудования: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# @login_required
# @require_http_methods(["POST"])
# def edit_booking(request, booking_id):
#     logger.info(f"Начало редактирования бронирования {booking_id} пользователем {request.user.phone_number}")
#     try:
#         booking = get_object_or_404(Booking, id=booking_id)
#         if not (request.user.is_staff or request.user.is_superuser):
#             logger.warning(f"Попытка редактирования бронирования {booking_id} без прав: {request.user.phone_number}")
#             return JsonResponse({'success': False, 'error': 'Нет прав для редактирования'}, status=403)
#
#         data = json.loads(request.body)
#         user_id = data.get('user')
#         service_id = data.get('service')
#         equipment_id = data.get('equipment')
#         start_date_str = data.get('start_date')
#         duration_type = data.get('duration_type')
#
#         if not all([user_id, service_id, start_date_str, duration_type]):
#             logger.error(
#                 f"Недостаточно данных для бронирования {booking_id}: user={user_id}, service={service_id}, start_date={start_date_str}, duration_type={duration_type}")
#             return JsonResponse({'success': False, 'error': 'Все обязательные поля должны быть заполнены'}, status=400)
#
#         user = get_object_or_404(CustomUser, id=user_id)
#         service = get_object_or_404(Service, id=service_id)
#         equipment = get_object_or_404(Equipment, id=equipment_id) if equipment_id else None
#
#         if equipment_id and equipment not in service.equipment.all():
#             logger.error(f"Оборудование {equipment_id} не связано с услугой {service_id} для бронирования {booking_id}")
#             return JsonResponse({'success': False, 'error': 'Выбранное оборудование не связано с услугой'}, status=400)
#
#         naive_start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
#         start_date = timezone.make_aware(naive_start_date)
#
#         if duration_type == 'hour':
#             end_date = start_date + timedelta(hours=1)
#         elif duration_type == 'day':
#             end_date = start_date + timedelta(days=1)
#         else:
#             logger.error(f"Недопустимый duration_type для бронирования {booking_id}: {duration_type}")
#             return JsonResponse({'success': False, 'error': 'Недопустимый тип длительности'}, status=400)
#
#         conflicting_bookings = Booking.objects.filter(
#             service=service,
#             start_date__lt=end_date,
#             end_date__gt=start_date
#         ).exclude(id=booking.id)
#         if conflicting_bookings.exists():
#             logger.error(f"Конфликт времени для услуги {service_id} в бронировании {booking_id}")
#             return JsonResponse({'success': False, 'error': 'Выбранное время уже занято для услуги'}, status=400)
#
#         if equipment_id:
#             conflicting_equipment = Booking.objects.filter(
#                 equipment=equipment,
#                 start_date__lt=end_date,
#                 end_date__gt=start_date
#             ).exclude(id=booking.id)
#             if conflicting_equipment.exists():
#                 logger.error(f"Конфликт оборудования {equipment_id} в бронировании {booking_id}")
#                 return JsonResponse({'success': False, 'error': 'Выбранное оборудование занято'}, status=400)
#
#         booking.user = user
#         booking.service = service
#         booking.equipment = equipment
#         booking.start_date = start_date
#         booking.end_date = end_date
#         booking.duration_type = duration_type
#         booking.save()
#
#         logger.info(f"Бронирование {booking_id} успешно обновлено пользователем {request.user.phone_number}")
#         return JsonResponse({'success': True, 'message': 'Бронирование успешно обновлено'})
#     except ValueError as e:
#         logger.error(f"Ошибка редактирования бронирования {booking_id}: {str(e)}")
#         return JsonResponse({'success': False, 'error': str(e)}, status=400)
#     except Exception as e:
#         logger.error(f"Неизвестная ошибка редактирования бронирования {booking_id}: {str(e)}")
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)

# @login_required
# @require_POST
# def delete_booking(request, booking_id):
#     logger.info(f"Удаление бронирования {booking_id} пользователем {request.user.phone_number}")
#     try:
#         booking = get_object_or_404(Booking, id=booking_id)
#         if not (request.user.is_staff or request.user.is_superuser):
#             logger.warning(f"Попытка удаления бронирования {booking_id} без прав: {request.user.phone_number}")
#             return JsonResponse({'success': False, 'error': 'Нет прав для удаления'}, status=403)
#
#         booking.delete()
#         logger.info(f"Бронирование {booking_id} успешно удалено пользователем {request.user.phone_number}")
#         return JsonResponse({'success': True, 'message': 'Бронирование успешно удалено'})
#     except Exception as e:
#         logger.error(f"Ошибка удаления бронирования {booking_id}: {str(e)}")
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)

# @login_required
# @require_http_methods(["POST"])
# def create_booking(request):
#     logger.info(f"Создание бронирования пользователем {request.user.phone_number}")
#     try:
#         if not (request.user.is_staff or request.user.is_superuser):
#             logger.warning(f"Попытка создания бронирования без прав: {request.user.phone_number}")
#             return JsonResponse({'success': False, 'error': 'Нет прав для создания'}, status=403)
#
#         data = json.loads(request.body)
#         user_id = data.get('user')
#         service_id = data.get('service')
#         equipment_id = data.get('equipment')
#         start_date_str = data.get('start_date')
#         duration_type = data.get('duration_type')
#
#         if not all([user_id, service_id, start_date_str, duration_type]):
#             logger.error(f"Недостаточно данных для бронирования: user={user_id}, service={service_id}, start_date={start_date_str}, duration_type={duration_type}")
#             return JsonResponse({'success': False, 'error': 'Все обязательные поля должны быть заполнены'}, status=400)
#
#         user = get_object_or_404(CustomUser, id=user_id)
#         service = get_object_or_404(Service, id=service_id)
#         equipment = get_object_or_404(Equipment, id=equipment_id) if equipment_id else None
#
#         if equipment_id and equipment not in service.equipment.all():
#             logger.error(f"Оборудование {equipment_id} не связано с услугой {service_id}")
#             return JsonResponse({'success': False, 'error': 'Выбранное оборудование не связано с услугой'}, status=400)
#
#         naive_start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
#         start_date = timezone.make_aware(naive_start_date)
#
#         if duration_type == 'hour':
#             end_date = start_date + timedelta(hours=1)
#         elif duration_type == 'day':
#             end_date = start_date + timedelta(days=1)
#         else:
#             logger.error(f"Недопустимый duration_type: {duration_type}")
#             return JsonResponse({'success': False, 'error': 'Недопустимый тип длительности'}, status=400)
#
#         conflicting_bookings = Booking.objects.filter(
#             service=service,
#             start_date__lt=end_date,
#             end_date__gt=start_date
#         )
#         if conflicting_bookings.exists():
#             logger.error(f"Конфликт времени для услуги {service_id}")
#             return JsonResponse({'success': False, 'error': 'Выбранное время уже занято для услуги'}, status=400)
#
#         if equipment_id:
#             conflicting_equipment = Booking.objects.filter(
#                 equipment=equipment,
#                 start_date__lt=end_date,
#                 end_date__gt=start_date
#             )
#             if conflicting_equipment.exists():
#                 logger.error(f"Конфликт оборудования {equipment_id}")
#                 return JsonResponse({'success': False, 'error': 'Выбранное оборудование занято'}, status=400)
#
#         booking = Booking.objects.create(
#             user=user,
#             service=service,
#             equipment=equipment,
#             start_date=start_date,
#             end_date=end_date,
#             duration_type=duration_type
#         )
#
#         logger.info(f"Бронирование {booking.id} успешно создано пользователем {request.user.phone_number}")
#         return JsonResponse({'success': True, 'message': 'Бронирование успешно создано'})
#     except ValueError as e:
#         logger.error(f"Ошибка создания бронирования: {str(e)}")
#         return JsonResponse({'success': False, 'error': str(e)}, status=400)
#     except Exception as e:
#         logger.error(f"Неизвестная ошибка создания бронирования: {str(e)}")
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return reverse_lazy('bookings_admin')
        return reverse_lazy('profile')

def services_view(request):
    services = Service.objects.all()
    service_types = ServiceType.objects.all()
    bookings = Booking.objects.filter(user=request.user) if request.user.is_authenticated else None
    return render(request, 'services.html',
                  {'services': services, 'service_types': service_types, 'bookings': bookings})

@login_required
def get_service(request, service_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    try:
        service = get_object_or_404(Service, id=service_id)
        prices = service.prices.all()
        price = prices.first() if prices.exists() else None
        return JsonResponse({
            'success': True,
            'service': {
                'name': service.name,
                'service_type_id': service.service_type_id,
                'description': service.description,
                'price_per_hour': str(price.price_per_hour) if price else '0.00',
                'price_per_day': str(price.price_per_day) if price else '0.00'
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
            description=description
        )
        service.prices.add(price)
        return JsonResponse({'success': True, 'id': service.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

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
        service.save()

        prices = service.prices.all()
        price = prices.first() if prices.exists() else None
        if price:
            price.price_per_hour = price_per_hour
            price.price_per_day = price_per_day
            price.save()
        else:
            price = Price.objects.create(
                name=f"Цена для {name}",
                price_per_hour=price_per_hour,
                price_per_day=price_per_day
            )
            service.prices.add(price)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def delete_service(request, service_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    try:
        service = get_object_or_404(Service, id=service_id)
        if Booking.objects.filter(service=service).exists():
            return JsonResponse({'success': False, 'error': 'Нельзя удалить услугу с активными бронированиями'},
                                status=400)
        service.delete()
        return JsonResponse({'success': True})
    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Услуга не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
                if user.is_superuser or user.is_staff:
                    return redirect('bookings_admin')
                return redirect('profile')
            else:
                messages.error(request, 'Ошибка аутентификации после регистрации.')
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
            end_date__gte=timezone.now()
        ) | Booking.objects.filter(
            user=self.request.user,
            end_date__isnull=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = {s.id: s for s in Service.objects.all()}
        context['equipment'] = {e.id: e for e in Equipment.objects.all()}
        return context

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

            conflicting_bookings = Booking.objects.filter(
                service=service,
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
                duration_type=duration_type
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
                duration_type=duration_type
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
            service.prices.add(price)
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
        return JsonResponse({'success': False, 'error': 'Цена не найдена'}, status=404)
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
        return JsonResponse({'success': False, 'error': 'Цена не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)