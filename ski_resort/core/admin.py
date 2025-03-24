# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, EquipmentHourly, EquipmentDaily, Service, Review, Booking

# Кастомный админ-класс для CustomUser (без изменений)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'username', 'first_name', 'last_name', 'is_staff', 'is_superuser') # поля показывать в списке пользователей
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Персональная информация', {'fields': ('username', 'first_name', 'last_name')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    ) # группировка полей на странице редактирования
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    ) # поля при создании нового пользователя
    search_fields = ('phone_number', 'username', 'first_name', 'last_name') # по каким полям можно искать
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups') # по каким полям фильтровать
    ordering = ('phone_number',) # сортировка по умолчанию

# Регистрируем CustomUser
admin.site.register(CustomUser, CustomUserAdmin)

# Регистрируем Role
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_code', 'role_name')
    search_fields = ('role_code', 'role_name')

# Регистрируем EquipmentHourly
@admin.register(EquipmentHourly)
class EquipmentHourlyAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_hour', 'available')
    list_filter = ('available',)
    search_fields = ('name', 'description')

# Регистрируем EquipmentDaily
@admin.register(EquipmentDaily)
class EquipmentDailyAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day', 'available')
    list_filter = ('available',)
    search_fields = ('name', 'description')

# Регистрируем Service
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'price')
    list_filter = ('type',)
    search_fields = ('name', 'description')

# Регистрируем Review
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'rating', 'created_at', 'approved')
    list_filter = ('approved', 'rating')
    search_fields = ('title', 'content', 'user__phone_number')

# Регистрируем Booking
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'equipment_hourly', 'equipment_daily', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('user__phone_number', 'service__name', 'equipment_hourly__name', 'equipment_daily__name')