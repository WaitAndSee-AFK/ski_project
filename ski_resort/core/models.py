# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Оценка от 1 до 5
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Equipment(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Цена за день"
    )
    available = models.BooleanField(default=True, verbose_name="Доступно")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Снаряжение"
        verbose_name_plural = "Снаряжение"


class Service(models.Model):
    SERVICE_TYPES = (
        ('rental', 'Прокат'),
        ('parking', 'Стоянка'),
    )
    name = models.CharField(max_length=100, verbose_name="Название")
    type = models.CharField(max_length=20, choices=SERVICE_TYPES, verbose_name="Тип")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Цена"
    )
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Услуга")
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Снаряжение")
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"Бронирование {self.id} - {self.user.username}"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"