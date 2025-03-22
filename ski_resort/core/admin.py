from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, Equipment, Service, Review, Booking


class CustomUserAdmin(UserAdmin):
    # Поля, которые будут отображаться в списке пользователей
    list_display = ('phone_number', 'username', 'first_name', 'last_name', 'is_staff', 'is_superuser')

    # Поля, которые можно редактировать в форме редактирования пользователя
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Персональная информация', {'fields': ('username', 'first_name', 'last_name')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Поля, которые отображаются при добавлении нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_staff',
                       'is_superuser'),
        }),
    )

    # Поля, по которым можно искать пользователей
    search_fields = ('phone_number', 'username', 'first_name', 'last_name')

    # Фильтры в боковой панели
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    # Поле, используемое для сортировки
    ordering = ('phone_number',)

    # Указываем, какое поле использовать для аутентификации
    filter_horizontal = ('groups', 'user_permissions',)


# Регистрируем модель CustomUser с кастомным админ-классом
admin.site.register(CustomUser, CustomUserAdmin)


# Регистрируем остальные модели
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_code', 'role_name')
    search_fields = ('role_code', 'role_name')


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day', 'available')
    list_filter = ('available',)
    search_fields = ('name', 'description')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'price')
    list_filter = ('type',)
    search_fields = ('name', 'description')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'rating', 'created_at', 'approved')
    list_filter = ('approved', 'rating')
    search_fields = ('title', 'content', 'user__phone_number')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'equipment', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('user__phone_number', 'service__name', 'equipment__name')