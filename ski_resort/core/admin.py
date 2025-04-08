from django.contrib import admin
from .models import CustomUser, Role, Price, ServiceType, Service, Equipment, Review, Booking

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'first_name', 'last_name', 'role_id', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'role_id')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name')
    search_fields = ('role_name',)
    ordering = ('id',)

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
    list_display = ('id', 'name', 'service_type_id', 'price_id', 'description')
    list_filter = ('service_type_id',)
    search_fields = ('name', 'description')
    ordering = ('id',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'service_id', 'size', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'size')
    list_editable = ('status',)
    ordering = ('id',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user_id', 'rating', 'created_at', 'approved')
    list_filter = ('approved', 'rating')
    search_fields = ('title', 'content', 'user_id')
    list_editable = ('approved',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(approved=True)
    approve_selected.short_description = "Одобрить выбранные отзывы"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'service_id', 'equipment_id', 'status', 'start_date', 'end_date', 'total_cost')
    list_filter = ('status', 'duration_type')
    search_fields = ('user_id', 'service_id', 'equipment_id')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    fieldsets = (
        (None, {
            'fields': ('user_id', 'service_id', 'equipment_id', 'status')
        }),
        ('Даты и стоимость', {
            'fields': ('start_date', 'end_date', 'duration_type', 'total_cost'),
            'classes': ('collapse',)
        }),
    )