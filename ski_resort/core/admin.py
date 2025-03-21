from django.contrib import admin
from .models import Equipment, Service, Booking
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'rating', 'approved', 'created_at')
    list_filter = ('approved', 'rating')
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(approved=True)
    approve_reviews.short_description = "Одобрить выбранные отзывы"

# Регистрация модели Equipment
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day', 'available')
    list_filter = ('available',)
    search_fields = ('name', 'description')

# Регистрация модели Service
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'price')
    list_filter = ('type',)
    search_fields = ('name', 'description')

# Регистрация модели Booking
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'equipment', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('user__username', 'service__name', 'equipment__name')