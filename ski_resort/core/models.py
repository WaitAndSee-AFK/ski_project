# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator

# для регистрация супер пользоваетля
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):

        if not phone_number:
            raise ValueError('Номер телефона должен быть указан')

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

# обыкновенный пользователь
class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True, verbose_name="Имя пользователя")
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Фамилия")

    USERNAME_FIELD = 'phone_number'  # Оставляем phone_number как поле для аутентификации
    REQUIRED_FIELDS = ['first_name', 'username']  # Добавляем username в обязательные поля

    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

# роль
class Role(models.Model):
    role_code = models.CharField(max_length=10, unique=True, verbose_name="Код роли")
    role_name = models.CharField(max_length=50, verbose_name="Наименование роли")

    def __str__(self):
        return f"{self.role_name} ({self.role_code})"

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

# (цены за час)
class EquipmentHourly(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Цена за час"
    )
    available = models.BooleanField(default=True, verbose_name="Доступно")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Цена (почасовая оплата)"
        verbose_name_plural = "Цены (почасовая оплата)"

# (цены за день)
class EquipmentDaily(models.Model):
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
        verbose_name = "Цена (посуточная оплата)"
        verbose_name_plural = "Цены (посуточная оплата)"

# услуги
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

# отзыв
class Review(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=100, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Оценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    approved = models.BooleanField(default=False, verbose_name="Одобрено")

    def __str__(self):
        return f"{self.title} - {self.user.phone_number}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

# бронирования
class Booking(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name="Пользователь")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Услуга")
    equipment_hourly = models.ForeignKey(EquipmentHourly, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Снаряжение (почасовая оплата)")
    equipment_daily = models.ForeignKey(EquipmentDaily, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Снаряжение (посуточная оплата)")
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"Бронирование {self.id} - {self.user.phone_number}"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"