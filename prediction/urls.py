from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'prediction'

urlpatterns = [
    path('predict/<int:patient_id>/', views.predict_image, name='predict_image'),  # Prediction form
    path('result/<int:prediction_id>/', views.result, name='result'),  # Prediction result page
]

 