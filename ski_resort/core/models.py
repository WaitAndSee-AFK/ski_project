# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('Номер телефона обязателен'))
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', None)  # Суперюзеры без роли
        return self.create_user(phone_number, password, **extra_fields)

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

class CustomUser(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
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
    REQUIRED_FIELDS = ['first_name']
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = None  # Суперюзеры без роли
        elif not self.role and not self.is_superuser:
            default_role, _ = Role.objects.get_or_create(role_name="Клиент")
            self.role = default_role
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Price(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Цена за час")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Цена за день")

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
        return self.name

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"

class Review(models.Model):
    title = models.CharField(max_length=100, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Рейтинг")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    approved = models.BooleanField(default=False, verbose_name="Одобрен")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

class Booking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Услуга")
    equipment = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Оборудование")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата начала")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата окончания")
    duration_type = models.CharField(
        max_length=10,
        choices=[('hour', 'Час'), ('day', 'День')],
        default='hour',
        blank=True,
        verbose_name="Тип длительности"
    )

    def __str__(self):
        return f"Бронирование {self.id}"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"