# core/urls.py
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
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Используем CustomLoginView
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('cancel_booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('bookings_admin/', views.AdminBookingsView.as_view(), name='bookings_admin'),
    path('edit_booking/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('book/equipment/<int:equipment_id>/', views.BookServiceView.as_view(), name='book_equipment'),
    path('prices/create/', views.create_price, name='create_price'),
    path('prices/update/<int:pk>/', views.update_price, name='update_price'),
    path('prices/delete/<int:pk>/', views.delete_price, name='delete_price'),
]

# urlpatterns = [
#     path('', views.HomeView.as_view(), name='home'),
#     path('reviews/', views.review_list, name='review_list'),
#     path('reviews/create/', views.create_review, name='create_review'),
#     path('reviews/moderation/', views.review_moderation, name='review_moderation'),
#     path('services/', views.services_view, name='services'),
#     path('add_service/', views.add_service, name='add_service'),
#     path('edit_service/<int:service_id>/', views.edit_service, name='edit_service'),
#     path('get_service/<int:service_id>/', views.get_service, name='get_service'),
#     path('delete_service/<int:service_id>/', views.delete_service, name='delete_service'),
#     path('book_service/<int:service_id>/', views.book_service, name='book_service'),
#     path('pricing/', views.PricingView.as_view(), name='pricing'),
#     path('login/', LoginView.as_view(template_name='login.html'), name='login'),
#     path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
#     path('register/', views.RegisterView.as_view(), name='register'),
#     path('cancel_booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
#     path('profile/', views.ProfileView.as_view(), name='profile'),
#     path('bookings_admin/', views.AdminBookingsView.as_view(), name='bookings_admin'),
#     path('edit_booking/<int:booking_id>/', views.edit_booking, name='edit_booking'),
#     path('book_service/<int:service_id>/', views.book_service, name='book_service'),
#     path('book/equipment/<int:equipment_id>/', views.BookServiceView.as_view(), name='book_equipment'),
#     path('prices/create/', views.create_price, name='create_price'),
#     path('prices/update/<int:pk>/', views.update_price, name='update_price'),
#     path('prices/delete/<int:pk>/', views.delete_price, name='delete_price'),
#     path('get_service/<int:service_id>/', views.get_service, name='get_service'),
# ]
