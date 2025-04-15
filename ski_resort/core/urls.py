from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/create/', views.create_review, name='create_review'),
    path('reviews/moderation/', views.review_moderation, name='review_moderation'),
    path('services/', views.services_view, name='services'),
    path('add_service/', views.add_service, name='add_service'),
    path('edit_service/<int:service_id>/', views.edit_service, name='edit_service'),
    path('get_service/<int:service_id>/', views.get_service, name='get_service'),
    path('delete_service/<int:service_id>/', views.delete_service, name='delete_service'),
    path('book_service/<int:service_id>/', views.book_service, name='book_service'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('bookings_admin/', views.bookings_view, name='bookings_admin'),
    path('prices/create/', views.create_price, name='create_price'),
    path('prices/update/<int:pk>/', views.update_price, name='update_price'),
    path('prices/delete/<int:pk>/', views.delete_price, name='delete_price'),
    path('get_available_services/', views.get_available_services, name='get_available_services'),
    path('get_available_equipment/', views.get_available_equipment, name='get_available_equipment'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/create/', views.create_booking, name='create_booking'),
    path('bookings/edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('bookings/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
]
