from django.urls import path
from dashboard.views import *

app_name = 'dashboard'

urlpatterns = [
    path("", dashboard_home, name="home_dashboard"),
    path('patient-details/', add_patient, name='patient-data'), 
    path('profile/', profile, name='profile'),
    path('patients/', patient_list, name='patient-list'),
    path('login/', login_page, name="login-page"),
    path('register/', register, name="register"),  
    path('logout/', logout_page, name="logout-page") , 
    path('patient/<int:patient_id>/', patient_profile, name='patient_profile'),
    path("delete-patient/<int:uId>/", delete, name="delete-patient"), 
    path("update-patient/<int:id>/", update, name="update-patient"),
    path('predictions/', prediction_list, name='prediction_list'),
    path('svm/', modelinfo, name='modelinfo'),
    path("delete-prediction/<int:prediction_id>/", delete_prediction, name="delete-prediction"),
    path("delete-prediction-id/<int:prediction_id>/", deletePrediction, name="delete-prediction-user"),
    
]
