from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# Менеджер пользователей
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('Номер телефона должен быть указан'))

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_superuser=True.'))

        return self.create_user(phone_number, password, **extra_fields)

# Роль
class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, verbose_name=_("Название роли"))  # "Сотрудник", "Клиент"

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = _("Роль")
        verbose_name_plural = _("Роли")

# Пользователь
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, verbose_name=_("Номер телефона"))
    first_name = models.CharField(max_length=30, blank=True, verbose_name=_("Имя"))
    last_name = models.CharField(max_length=30, blank=True, verbose_name=_("Фамилия"))
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_DEFAULT,
        default=1,  # Предполагается, что ID 1 будет соответствовать роли "Клиент"
        verbose_name=_("Роль")
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")

# Цены
class Price(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Цена за час")
    )
    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Цена за день")
    )

    def __str__(self):
        return f"{self.name} ({self.price_per_hour}/{self.price_per_day})"

    class Meta:
        verbose_name = _("Цена")
        verbose_name_plural = _("Цены")

    def delete(self, *args, **kwargs):
        if self.services.exists():
            raise ValidationError(_("Нельзя удалить цену, так как есть связанные услуги"))
        super().delete(*args, **kwargs)

# Новая модель Тип услуги
class ServiceType(models.Model):
    SERVICE_TYPE_CHOICES = (
        ('rental', _('Прокат')),
        ('parking', _('Стоянка автомобиля')),
    )
    name = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        unique=True,
        verbose_name=_("Название типа услуги")
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = _("Тип услуги")
        verbose_name_plural = _("Типы услуг")

# Услуга
class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        verbose_name=_("Тип услуги"),
        related_name='services'
    )
    price = models.ForeignKey(
        Price,
        on_delete=models.PROTECT,
        verbose_name=_("Цена"),
        related_name='services'
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))

    def __str__(self):
        return f"{self.name} ({self.service_type.get_name_display()})"

    def clean(self):
        super().clean()
        if not Price.objects.filter(id=self.price_id).exists():
            raise ValidationError(_("Указанная цена не существует"))

    class Meta:
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")

# Оборудование
class Equipment(models.Model):
    EQUIPMENT_STATUS = (
        ('ready', _('Готово к эксплуатации')),
        ('repair', _('В ремонте')),
    )
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        verbose_name=_("Услуга"),
        related_name='equipment'
    )
    size = models.CharField(max_length=10, blank=True, verbose_name=_("Размер"))
    status = models.CharField(max_length=10, choices=EQUIPMENT_STATUS, default='ready', verbose_name=_("Состояние"))

    def is_available(self, start_date, end_date):
        return not self.bookings.filter(
            start_date__lt=end_date,
            end_date__gt=start_date,
            status='active'
        ).exists()

    def __str__(self):
        return f"{self.name} ({self.size}) - {self.status}"

    class Meta:
        verbose_name = _("Оборудование")
        verbose_name_plural = _("Оборудование")

# Отзывы
class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name=_("Пользователь"))
    title = models.CharField(max_length=100, verbose_name=_("Заголовок"))
    content = models.TextField(verbose_name=_("Содержание"))
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name=_("Оценка"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    approved = models.BooleanField(default=False, verbose_name=_("Одобрено"))

    def __str__(self):
        return f"{self.title} - {self.user.phone_number}"

    class Meta:
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")

# Бронирование
class Booking(models.Model):
    STATUS_CHOICES = (
        ('active', _('Активно')),
        ('completed', _('Завершено')),
        ('canceled', _('Отменено')),
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь"),
        related_name='bookings'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        verbose_name=_("Услуга"),
        related_name='bookings'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Оборудование"),
        related_name='bookings'
    )
    start_date = models.DateTimeField(verbose_name=_("Дата начала"))
    end_date = models.DateTimeField(verbose_name=_("Дата окончания"))
    duration_type = models.CharField(
        max_length=10,
        choices=[('hour', _('Час')), ('day', _('День'))],
        default='hour',
        verbose_name=_("Тип длительности")
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Общая стоимость"),
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_("Статус")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))

    def __str__(self):
        return f"Бронирование {self.id} - {self.user.phone_number}"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError(_("Дата окончания должна быть позже даты начала."))

        if self.equipment and self.equipment.status == 'repair':
            raise ValidationError(_("Выбранное оборудование находится в ремонте."))

        if self.equipment and not self.equipment.is_available(self.start_date, self.end_date):
            raise ValidationError(_("Оборудование уже занято в выбранный период"))

    def save(self, *args, **kwargs):
        self.total_cost = self.calculate_cost()
        super().save(*args, **kwargs)

    def calculate_cost(self):
        if not self.service or not self.start_date or not self.end_date:
            return 0

        duration = self.end_date - self.start_date
        if self.duration_type == 'hour':
            hours = max(1, duration.total_seconds() / 3600)
            return round(float(self.service.price.price_per_hour) * hours, 2)
        else:
            days = max(1, duration.days + (1 if duration.seconds > 0 else 0))
            return round(float(self.service.price.price_per_day) * days, 2)

    class Meta:
        verbose_name = _("Бронирование")
        verbose_name_plural = _("Бронирования")
        ordering = ['-created_at']