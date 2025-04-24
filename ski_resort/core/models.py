# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('Номер телефона обязателен'))

        # Нормализация номера телефона
        phone_number = self.normalize_phone_number(phone_number)

        if not self.validate_phone_number(phone_number):
            raise ValidationError(_('Неверный формат номера телефона'))

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', None)
        return self.create_user(phone_number, password, **extra_fields)

    @staticmethod
    def normalize_phone_number(phone):
        """Приводит номер к формату +7XXXXXXXXXX"""
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) == 11:
            if phone.startswith('8'):
                return '+7' + phone[1:]
            elif phone.startswith('7'):
                return '+' + phone
        return phone

    @staticmethod
    def validate_phone_number(phone):
        """Проверяет валидность номера телефона"""
        phone = ''.join(filter(str.isdigit, phone))
        return len(phone) == 11 and phone.startswith('7')


class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"


class CustomUser(AbstractUser):
    username = None
    phone_regex = RegexValidator(
        regex=r'^\+7\d{10}$',  # Точный формат +7XXXXXXXXXX (11 цифр с +7)
        message="Номер должен быть в формате: '+79991234567' (ровно 11 цифр)"
    )

    phone_number = models.CharField(
        max_length=12,  # +7 + 10 цифр
        unique=True,
        validators=[phone_regex],
        verbose_name="Номер телефона"
    )
    first_name = models.CharField(max_length=30, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Фамилия")
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Роль"
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def clean(self):
        super().clean()
        self.phone_number = self.__class__.objects.normalize_phone_number(self.phone_number)
        if not self.__class__.objects.validate_phone_number(self.phone_number):
            raise ValidationError({'phone_number': 'Неверный формат номера телефона'})

    def save(self, *args, **kwargs):
        self.phone_number = self.__class__.objects.normalize_phone_number(self.phone_number)
        if self.is_superuser:
            self.role = None
        elif not self.role and not self.is_superuser:
            default_role, _ = Role.objects.get_or_create(role_name="Клиент")
            self.role = default_role
        super().save(*args, **kwargs)

    def __str__(self):
        return f"+7{self.phone_number[1:]}"  # Форматированный вывод номера

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Price(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
                                         verbose_name="Цена за час")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
                                        verbose_name="Цена за день")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "Цены"


class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип услуги"
        verbose_name_plural = "Типы услуг"


class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, verbose_name="Тип услуги")
    equipment = models.ManyToManyField('Equipment', blank=True, verbose_name="Оборудование")
    prices = models.ManyToManyField(Price, blank=True, verbose_name="Цены")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Equipment(models.Model):
    EQUIPMENT_STATUS = (
        ('ready', 'Готов к использованию'),
        ('repair', 'В ремонте'),
    )
    name = models.CharField(max_length=100, verbose_name="Название")
    size = models.CharField(max_length=10, blank=True, verbose_name="Размер")
    status = models.CharField(max_length=10, choices=EQUIPMENT_STATUS, default='ready', verbose_name="Статус")

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"


class Review(models.Model):
    title = models.CharField(max_length=100, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Рейтинг")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    approved = models.BooleanField(default=False, verbose_name="Одобрен")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Пользователь")

    def __str__(self):
        return f"{self.title} ({self.user.phone_number})"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Подтверждено'),
        ('completed', 'Завершено'),
        ('canceled', 'Отменено'),
    ]

    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='bookings'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.PROTECT,
        verbose_name="Услуга",
        related_name='bookings'
    )
    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Оборудование",
        related_name='bookings'
    )
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    duration_type = models.CharField(
        max_length=10,
        choices=[('hour', 'Час'), ('day', 'День')],
        default='hour',
        verbose_name="Тип длительности"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='confirmed',
        verbose_name="Статус бронирования",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )

    def clean(self):
        super().clean()

        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("Дата окончания должна быть позже даты начала.")

    def save(self, *args, **kwargs):
        # Для новых бронирований устанавливаем статус "confirmed", если он не указан
        if self._state.adding and self.status is None:
            self.status = 'confirmed'
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone_number} - {self.service.name} ({self.start_date.strftime('%d.%m.%Y %H:%M')})"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
