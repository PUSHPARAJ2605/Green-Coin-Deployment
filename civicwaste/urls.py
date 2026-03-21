from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/rewards/', include('rewards.urls')),
    
    # Frontend Routes
    path('', TemplateView.as_view(template_name='landing.html'), name='landing_page'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login_page'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register_page'),
    path('dashboard/citizen/', TemplateView.as_view(template_name='citizen/dashboard.html'), name='citizen_dashboard'),
    path('dashboard/collector/', TemplateView.as_view(template_name='collector/dashboard.html'), name='collector_dashboard'),
    path('success/', TemplateView.as_view(template_name='success.html'), name='success_page'),
    path('collector/success/', TemplateView.as_view(template_name='collector_success.html'), name='collector_success_page'),
    path('redeem/', TemplateView.as_view(template_name='redeem.html'), name='redeem_page'),

    path('redeem/success/', TemplateView.as_view(template_name='redeem_success.html'), name='redeem_success_page'),
    path('penalty/', TemplateView.as_view(template_name='penalty.html'), name='penalty_page'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
