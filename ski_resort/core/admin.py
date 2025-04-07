from django.contrib import admin
from .models import CustomUser, Role, Price, Service, ServiceType, Equipment, Review, Booking  # Добавили ServiceType

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    search_fields = ['phone_number', 'first_name', 'last_name']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['role_name']
    search_fields = ['role_name']

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_per_hour', 'price_per_day']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'price_display']
    list_filter = ['service_type']
    search_fields = ['name']

    def price_display(self, obj):
        return f"{obj.price.price_per_hour} / {obj.price.price_per_day}" if obj.price else "Нет цены"
    price_display.short_description = 'Цена (час/день)'

@admin.register(ServiceType)  # Добавили регистрацию ServiceType
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name']  # Отображаем поле name
    search_fields = ['name']  # Поиск по имени

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'size', 'status']
    list_filter = ['status', 'service']
    search_fields = ['name', 'service__name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'rating', 'created_at', 'approved']
    list_filter = ['approved', 'rating']
    search_fields = ['title', 'user__phone_number', 'content']

    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(approved=True)
    approve_reviews.short_description = "Одобрить выбранные отзывы"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'equipment', 'start_date', 'end_date', 'duration_type', 'status', 'total_cost']
    list_filter = ['status', 'duration_type', 'service']
    search_fields = ['user__phone_number', 'service__name', 'equipment__name']

    fieldsets = (
        (None, {
            'fields': ('user', 'service', 'equipment')
        }),
        ('Даты и стоимость', {
            'fields': ('start_date', 'end_date', 'duration_type', 'total_cost')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)