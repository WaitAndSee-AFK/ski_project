from django.contrib import admin
from .models import (
    Role, CustomUser, Price, ServiceType,
    Service, Equipment, Review, Booking
)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name')
    search_fields = ('role_name',)
    ordering = ('id',)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'role')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price_per_hour', 'price_per_day')
    list_editable = ('price_per_hour', 'price_per_day')
    search_fields = ('name',)
    ordering = ('id',)

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('id',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'service_type')
    search_fields = ('name', 'description')
    list_filter = ('service_type',)
    filter_horizontal = ('equipment', 'prices')
    ordering = ('id',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'size', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'size')
    list_editable = ('status',)
    ordering = ('id',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'rating', 'created_at', 'approved')
    list_filter = ('approved', 'rating', 'user')
    search_fields = ('title', 'content', 'user__phone_number')
    list_editable = ('approved',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(approved=True)
    approve_selected.short_description = "Одобрить выбранные отзывы"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'equipment', 'start_date', 'end_date', 'duration_type')
    list_filter = ('duration_type', 'service', 'equipment', 'user')
    search_fields = ('service__name', 'equipment__name', 'user__phone_number',
                    'user__first_name', 'user__last_name')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    fieldsets = (
        (None, {'fields': ('user', 'service', 'equipment', 'duration_type')}),
        ('Даты', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
    )