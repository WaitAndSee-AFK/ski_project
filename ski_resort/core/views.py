# core/views.py
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Equipment, Service, Booking
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ReviewForm
from .models import Review

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Booking


@csrf_exempt
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
            booking.delete()
            return JsonResponse({'success': True})
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Бронирование не найдено'})
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
            return redirect('review_list')
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form})


# Для администратора
def review_moderation(request):
    if request.user.is_staff:
        reviews = Review.objects.filter(approved=False)
        return render(request, 'review_moderation.html', {'reviews': reviews})
    return redirect('review_list')


class HomeView(View):
    def get(self, request):
        return render(request, 'home.html', {
            'complex_info': {
                'name': 'Горнолыжный курорт Алтай',
                'description': 'Лучший курорт в регионе с современным оборудованием и трассами',
                'location': 'Горы Алтая'
            }
        })


class ServicesView(ListView):
    model = Service
    template_name = 'services.html'
    context_object_name = 'services'


class PricingView(ListView):
    model = Equipment
    template_name = 'pricing.html'
    context_object_name = 'equipment'


class RegisterView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')
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
                item = Service.objects.get(id=service_id)
                booking_type = 'service'
            elif equipment_id:
                item = Equipment.objects.get(id=equipment_id)
                booking_type = 'equipment'
            else:
                raise ValueError("Не указан объект бронирования")

            booking = Booking.objects.create(
                user=request.user,
                service=item if booking_type == 'service' else None,
                equipment=item if booking_type == 'equipment' else None,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=1)
            )
            messages.success(request, 'Бронирование успешно создано!')
        except Exception as e:
            messages.error(request, f'Ошибка бронирования: {str(e)}')
        return redirect('profile')
