# core/admin.py
from django.contrib import admin
from .models import CustomUser, Role, UserRole, Price, Service, Equipment, Review, Booking

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'username', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['phone_number', 'username', 'first_name', 'last_name']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['role_name']
    search_fields = ['role_name']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']
    search_fields = ['user__phone_number', 'role__role_name']

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['description', 'price_per_hour', 'price_per_day']
    search_fields = ['description']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'price_display']
    list_filter = ['service_type']
    search_fields = ['name']

    def price_display(self, obj):
        return f"{obj.price.price_per_hour} / {obj.price.price_per_day}"
    price_display.short_description = 'Цена (час/день)'

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

