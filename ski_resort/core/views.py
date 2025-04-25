from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import ListView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json
import logging

from .models import Equipment, Service, Booking, Review, CustomUser, Price, ServiceType
from .forms import ReviewForm, BookingForm, CustomUserCreationForm


@login_required
@require_POST
def change_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('status')

    if new_status in dict(Booking.STATUS_CHOICES).keys():
        booking.status = new_status
        booking.save()
        messages.success(request, f'Статус бронирования успешно изменен на "{booking.get_status_display()}"')
    else:
        messages.error(request, 'Неверный статус бронирования')

    next_url = request.GET.get('next', reverse('bookings_admin'))
    return redirect(next_url)

logger = logging.getLogger(__name__)

def create_combined_booking(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, prefix='user')
        booking_form = BookingForm(request.POST, prefix='booking')

        # Логируем данные, отправленные в POST
        logger.debug(f"POST данные: {request.POST}")

        if user_form.is_valid() and booking_form.is_valid():
            try:
                # Проверяем, существует ли пользователь с таким номером телефона
                phone_number = user_form.cleaned_data.get('phone_number')
                if CustomUser.objects.filter(phone_number=phone_number).exists():
                    messages.error(request, 'Пользователь с таким номером телефона уже существует.')
                    return render(request, 'create_combined.html', {
                        'user_form': user_form,
                        'booking_form': booking_form,
                        'services': Service.objects.all(),
                        'equipment': Equipment.objects.all(),
                    })

                # Создаем пользователя
                user = user_form.save()

                # Создаем бронирование
                booking = booking_form.save(commit=False)
                booking.user = user  # Задаём пользователя
                booking.end_date = booking_form.cleaned_data['end_date']  # Устанавливаем end_date из формы
                booking.full_clean()  # Вызываем валидацию модели
                booking.save()

                messages.success(request, 'Пользователь и бронирование успешно созданы!')
                return redirect('booking_list')

            except Exception as e:
                logger.error(f"Ошибка при создании: {str(e)}")
                messages.error(request, f'Ошибка при создании: {str(e)}')
        else:
            # Логируем ошибки форм
            logger.error(f"Ошибки в формах: user - {user_form.errors}, booking - {booking_form.errors}")
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = CustomUserCreationForm(prefix='user')
        booking_form = BookingForm(prefix='booking', initial={
            'start_date': timezone.now() + timedelta(hours=1),
            'duration_type': 'hour',
        })

    return render(request, 'create_combined.html', {
        'user_form': user_form,
        'booking_form': booking_form,
        'services': Service.objects.all(),
        'equipment': Equipment.objects.all(),
    })


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


logger = logging.getLogger(__name__)

def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                # Создаём объект бронирования, но не сохраняем его сразу
                booking = form.save(commit=False)
                # Устанавливаем end_date из cleaned_data
                booking.end_date = form.cleaned_data['end_date']
                # Сохраняем объект
                booking.save()
                messages.success(request, 'Бронирование успешно создано!')
                return redirect('bookings_admin')
            except Exception as e:
                messages.error(request, f'Ошибка при создании бронирования: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = BookingForm(initial={
            'start_date': timezone.now() + timedelta(hours=1),
            'duration_type': 'hour',
        })

    return render(request, 'create_booking.html', {
        'form': form,
        'users': CustomUser.objects.all(),
        'services': Service.objects.all(),
        'equipment': Equipment.objects.all(),
    })


def edit_booking(request, booking_id):
    logger.info(f"Начало редактирования бронирования {booking_id} пользователем {request.user.phone_number}")
    booking = get_object_or_404(Booking, id=booking_id)

    # Проверка прав доступа
    if booking.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        logger.warning(
            f"Попытка редактирования бронирования {booking_id} без прав пользователем {request.user.phone_number}")
        return HttpResponseForbidden("У вас нет прав для редактирования этого бронирования")

    if request.method == 'POST':
        # Если это запрос на отмену
        if 'cancel_booking' in request.POST:
            booking.status = 'canceled'
            booking.save()
            messages.success(request, 'Бронирование успешно отменено.')
            logger.info(f"Бронирование {booking_id} отменено пользователем {request.user.phone_number}")
            return redirect('profile')

        # Если это обычное редактирование
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно обновлено.')
            if request.user.is_staff or request.user.is_superuser:
                return redirect('bookings_admin')
            return redirect('profile')
        else:
            messages.error(request, 'Ошибка при обновлении бронирования.')
            logger.error(f"Ошибка в форме: {form.errors}")
    else:
        form = BookingForm(instance=booking)

    return render(request, 'edit_booking.html', {
        'form': form,
        'booking': booking,
        'services': Service.objects.all(),
        'equipment': Equipment.objects.all(),
    })


def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Проверяем, что бронирование принадлежит пользователю, если он не staff и не superuser
    if not (request.user.is_staff or request.user.is_superuser) and booking.user != request.user:
        messages.error(request, 'У вас нет прав для удаления этого бронирования.')
        return redirect('profile')  # Перенаправляем на профиль в случае ошибки

    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Бронирование успешно удалено.')
        # Перенаправление в зависимости от роли пользователя
        if request.user.is_staff or request.user.is_superuser:
            return redirect('bookings_admin')  # Staff и superuser перенаправляются на booking_list
        else:
            return redirect('profile')  # Обычные пользователи перенаправляются на профиль
    else:
        # Если метод не POST, перенаправляем в зависимости от роли
        if request.user.is_staff or request.user.is_superuser:
            return redirect('booking_list')
        else:
            return redirect('profile')


logger = logging.getLogger(__name__)

@login_required
def bookings_view(request):
    logger.info(f"Запрос страницы бронирований от пользователя {request.user.phone_number}")
    if not (request.user.is_staff or request.user.is_superuser):
        logger.warning(f"Попытка доступа к странице бронирований без прав: {request.user.phone_number}")
        return HttpResponseForbidden("Доступ запрещён")

    # Получаем бронирования, разделенные по статусам
    active_bookings = Booking.objects.filter(
        Q(status='confirmed') | Q(status=None)
    ).select_related('user', 'service', 'equipment').order_by('-start_date')

    completed_bookings = Booking.objects.filter(
        status='completed'
    ).select_related('user', 'service', 'equipment').order_by('-start_date')

    canceled_bookings = Booking.objects.filter(
        status='canceled'
    ).select_related('user', 'service', 'equipment').order_by('-start_date')

    return render(request, 'admin_bookings.html', {
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'canceled_bookings': canceled_bookings,
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

        logger.info(
            f"Запрос оборудования: service_id={service_id}, start_date={start_date_str}, end_date={end_date_str}, exclude_booking_id={exclude_booking_id}")

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
@require_http_methods(["GET", "POST"])
def add_service(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав доступа'}, status=403)

    service_types = ServiceType.objects.all()
    equipment_list = Equipment.objects.all()
    prices = Price.objects.all()

    if request.method == "POST":
        try:
            name = request.POST.get('name')
            service_type_id = request.POST.get('service_type')
            description = request.POST.get('description')
            equipment_ids = request.POST.getlist('equipment')
            price_id = request.POST.get('price')

            if not all([name, service_type_id, price_id]):
                context = {
                    'error': 'Все обязательные поля должны быть заполнены',
                    'form_data': {
                        'name': name,
                        'service_type': service_type_id,
                        'description': description,
                        'equipment': equipment_ids,
                        'price': price_id,
                    },
                    'service_types': service_types,
                    'equipment_list': equipment_list,
                    'prices': prices,
                }
                return render(request, "add_service.html", context)

            # Создаем услугу
            service = Service.objects.create(
                name=name,
                service_type_id=service_type_id,
                description=description
            )

            # Связываем с оборудованием
            if equipment_ids:
                service.equipment.set(equipment_ids)

            # Связываем с выбранной ценой
            selected_price = Price.objects.get(id=price_id)
            service.prices.add(selected_price)

            return redirect('services')
        except Exception as e:
            context = {
                'error': f'Ошибка при создании услуги: {str(e)}',
                'service_types': service_types,
                'equipment_list': equipment_list,
                'prices': prices,
            }
            return render(request, "add_service.html", context)
    else:
        context = {
            'service_types': service_types,
            'equipment_list': equipment_list,
            'prices': prices,
        }
        return render(request, "add_service.html", context)

@login_required
@require_http_methods(["GET", "POST"])
def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("У вас нет прав для редактирования услуг")

    # Получаем данные для формы
    service_types = ServiceType.objects.all()
    equipment_list = Equipment.objects.filter(status='ready')
    prices = Price.objects.all()
    current_price = service.prices.first()  # Получаем текущую цену (или None)

    if request.method == "POST":
        form_data = {
            'name': request.POST.get('name'),
            'service_type': request.POST.get('service_type'),
            'description': request.POST.get('description'),
            'equipment': request.POST.getlist('equipment'),
            'price': request.POST.get('price'),
        }

        # Валидация обязательных полей
        required_fields = ['name', 'service_type', 'price']
        if not all(form_data[field] for field in required_fields):
            context = {
                'error': 'Пожалуйста, заполните все обязательные поля',
                'service': service,
                'service_types': service_types,
                'equipment_list': equipment_list,
                'prices': prices,
                'form_data': form_data,
            }
            return render(request, "edit_service.html", context)

        try:
            # Обновляем основную информацию об услуге
            service.name = form_data['name']
            service.service_type_id = form_data['service_type']
            service.description = form_data['description']
            service.save()

            # Обновляем связанное оборудование
            if form_data['equipment']:
                equipment_ids = [int(eq_id) for eq_id in form_data['equipment']]
                service.equipment.set(equipment_ids)
            else:
                service.equipment.clear()

            # Обновляем цену
            selected_price = get_object_or_404(Price, id=form_data['price'])
            service.prices.set([selected_price])

            messages.success(request, 'Услуга успешно обновлена!')
            return redirect('services')

        except Exception as e:
            context = {
                'error': f'Ошибка при обновлении услуги: {str(e)}',
                'service': service,
                'service_types': service_types,
                'equipment_list': equipment_list,
                'prices': prices,
                'form_data': form_data,
            }
            return render(request, "edit_service.html", context)

    else:  # GET-запрос
        form_data = {
            'name': service.name,
            'service_type': service.service_type.id if service.service_type else '',
            'description': service.description,
            'equipment': [str(eq.id) for eq in service.equipment.all()],
            'price': current_price.id if current_price else '',
        }

        context = {
            'service': service,
            'service_types': service_types,
            'equipment_list': equipment_list,
            'prices': prices,
            'form_data': form_data,
        }
        return render(request, "edit_service.html", context)

# @login_required
# @require_http_methods(["GET", "POST"])
# def edit_service(request, service_id):
#     service = get_object_or_404(Service, id=service_id)
#
#     if not (request.user.is_staff or request.user.is_superuser):
#         return HttpResponseForbidden("У вас нет прав для редактирования услуг")
#
#     # Получаем данные для формы
#     service_types = ServiceType.objects.all()
#     equipment_list = Equipment.objects.filter(status='ready')
#     prices = Price.objects.all()
#     current_price = service.prices.first()  # Получаем текущую цену (или None)
#
#     if request.method == "POST":
#         form_data = {
#             'name': request.POST.get('name'),
#             'service_type': request.POST.get('service_type'),
#             'description': request.POST.get('description'),
#             'equipment': request.POST.getlist('equipment'),
#             'price': request.POST.get('price'),
#         }
#
#         # Валидация обязательных полей
#         required_fields = ['name', 'service_type', 'price']
#         if not all(form_data[field] for field in required_fields):
#             context = {
#                 'error': 'Пожалуйста, заполните все обязательные поля',
#                 'service': service,
#                 'service_types': service_types,
#                 'equipment_list': equipment_list,
#                 'prices': prices,
#                 'form_data': form_data,
#             }
#             return render(request, "edit_service.html", context)
#
#         try:
#             # Обновляем основную информацию об услуге
#             service.name = form_data['name']
#             service.service_type_id = form_data['service_type']
#             service.description = form_data['description']
#             service.save()
#
#             # Обновляем связанное оборудование
#             if form_data['equipment']:
#                 equipment_ids = [int(eq_id) for eq_id in form_data['equipment']]
#                 service.equipment.set(equipment_ids)
#             else:
#                 service.equipment.clear()
#
#             # Обновляем цену
#             selected_price = get_object_or_404(Price, id=form_data['price'])
#             service.prices.set([selected_price])
#
#             messages.success(request, 'Услуга успешно обновлена!')
#             return redirect('services')
#
#         except Exception as e:
#             context = {
#                 'error': f'Ошибка при обновлении услуги: {str(e)}',
#                 'service': service,
#                 'service_types': service_types,
#                 'equipment_list': equipment_list,
#                 'prices': prices,
#                 'form_data': form_data,
#             }
#             return render(request, "edit_service.html", context)
#
#     else:  # GET-запрос
#         form_data = {
#             'name': service.name,
#             'service_type': service.service_type.id if service.service_type else '',
#             'description': service.description,
#             'equipment': [str(eq.id) for eq in service.equipment.all()],
#             'price': current_price.id if current_price else '',
#         }
#
#         context = {
#             'service': service,
#             'service_types': service_types,
#             'equipment_list': equipment_list,
#             'prices': prices,
#             'form_data': form_data,
#         }
#         return render(request, "edit_service.html", context)




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
def book_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    equipment = Equipment.objects.filter(status='ready')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        start_date_str = request.POST.get('start_date')

        if not start_date_str:
            messages.error(request, 'Не указана дата начала бронирования.')
            return render(request, 'book_service.html', {
                'form': form,
                'services': Service.objects.all(),
                'equipment': equipment,
            })

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            start_date = timezone.make_aware(start_date)

            if start_date < timezone.now():
                messages.error(request, 'Дата начала должна быть не раньше текущего времени.')
                return render(request, 'book_service.html', {
                    'form': form,
                    'services': Service.objects.all(),
                    'equipment': equipment,
                })

            duration_type = request.POST.get('booking-duration_type', 'hour')
            end_date = start_date + timedelta(hours=1) if duration_type == 'hour' else start_date + timedelta(days=1)

            # Фильтрация доступного оборудования
            booked_equipment = Booking.objects.filter(
                start_date__lt=end_date,
                end_date__gt=start_date
            ).exclude(equipment__isnull=True).values_list('equipment_id', flat=True)
            available_equipment = Equipment.objects.filter(status='ready').exclude(id__in=booked_equipment)
            form.fields['equipment'].queryset = available_equipment

            if form.is_valid():
                # Проверка конфликтов для услуги
                conflicting_bookings = Booking.objects.filter(
                    service=form.cleaned_data['service'],
                    start_date__lt=end_date,
                    end_date__gt=start_date
                )
                if conflicting_bookings.exists():
                    messages.error(request, 'Выбранное время уже занято для этой услуги.')
                    return render(request, 'book_service.html', {
                        'form': form,
                        'services': Service.objects.all(),
                        'equipment': available_equipment,
                    })

                # Проверка конфликтов для оборудования
                selected_equipment = form.cleaned_data['equipment']
                if selected_equipment:
                    conflicting_equipment = Booking.objects.filter(
                        equipment=selected_equipment,
                        start_date__lt=end_date,
                        end_date__gt=start_date
                    )
                    if conflicting_equipment.exists():
                        messages.error(request, 'Выбранное оборудование уже занято.')
                        return render(request, 'book_service.html', {
                            'form': form,
                            'services': Service.objects.all(),
                            'equipment': available_equipment,
                        })

                # Сохранение бронирования
                booking = form.save(commit=False)
                booking.user = request.user
                booking.end_date = end_date
                booking.save()
                messages.success(request, 'Бронирование успешно создано!')
                return redirect('profile')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
        except ValueError as e:
            messages.error(request, f'Неверный формат даты: {str(e)}')
    else:
        initial_start_date = timezone.now() + timedelta(hours=1)
        form = BookingForm(initial={
            'service': service,
            'start_date': initial_start_date,
            'duration_type': 'hour',
        })
        # Фильтрация доступного оборудования
        end_date = initial_start_date + timedelta(hours=1)
        booked_equipment = Booking.objects.filter(
            start_date__lt=end_date,
            end_date__gt=initial_start_date
        ).exclude(equipment__isnull=True).values_list('equipment_id', flat=True)
        form.fields['equipment'].queryset = Equipment.objects.filter(status='ready').exclude(id__in=booked_equipment)

    return render(request, 'book_service.html', {
        'form': form,
        'services': Service.objects.all(),
        'equipment': equipment,
    })


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
