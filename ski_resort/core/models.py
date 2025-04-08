from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('Номер телефона должен быть указан'))
        extra_fields.setdefault('role_id', 1)
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role_id', 1)
        return self.create_user(phone_number, password, **extra_fields)

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, verbose_name=_("Название роли"))

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = _("Роль")
        verbose_name_plural = _("Роли")

class CustomUser(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=15, unique=True, verbose_name=_("Номер телефона"))
    first_name = models.CharField(max_length=30, blank=True, verbose_name=_("Имя"))
    last_name = models.CharField(max_length=30, blank=True, verbose_name=_("Фамилия"))
    role_id = models.IntegerField(null=True, blank=True, default=1, verbose_name=_("Роль"))

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name']
    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")

class Price(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Цена")
        verbose_name_plural = _("Цены")

class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Наименование"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Вид услуг")
        verbose_name_plural = _("Виды услуг")

class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    service_type_id = models.IntegerField(null=True, blank=True, verbose_name=_("Вид услуги"))
    price_id = models.IntegerField(null=True, blank=True, verbose_name=_("Цена"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")

class Equipment(models.Model):
    EQUIPMENT_STATUS = (
        ('ready', _('Готово к эксплуатации')),
        ('repair', _('В ремонте')),
    )
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    service_id = models.IntegerField(null=True, blank=True, verbose_name=_("Услуга"))
    size = models.CharField(max_length=10, blank=True, verbose_name=_("Размер"))
    status = models.CharField(max_length=10, choices=EQUIPMENT_STATUS, default='ready')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Оборудование")
        verbose_name_plural = _("Оборудование")

class Review(models.Model):
    user_id = models.IntegerField(null=True, blank=True, verbose_name=_("Пользователь"))
    title = models.CharField(max_length=100, verbose_name=_("Заголовок"))
    content = models.TextField(verbose_name=_("Содержание"))
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")

class Booking(models.Model):
    STATUS_CHOICES = (
        ('active', _('Активно')),
        ('completed', _('Завершено')),
        ('canceled', _('Отменено')),
    )
    user_id = models.IntegerField(null=True, blank=True, verbose_name=_("Пользователь"))
    service_id = models.IntegerField(null=True, blank=True, verbose_name=_("Услуга"))
    equipment_id = models.IntegerField(null=True, blank=True, verbose_name=_("Оборудование"))
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    duration_type = models.CharField(max_length=10, choices=[('hour', _('Час')), ('day', _('День'))], default='hour')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Бронирование {self.id}"

    class Meta:
        verbose_name = _("Бронирование")
        verbose_name_plural = _("Бронирования")