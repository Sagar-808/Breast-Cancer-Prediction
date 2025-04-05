from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Patient
from prediction.models import Prediction
from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import reverse
from django.db import IntegrityError
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@login_required
def add_patient(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        age= request.POST.get('age')
        sex = request.POST.get('sex')
        uid = request.POST.get('uId')
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        picture = request.FILES.get('picture')

        if Patient.objects.filter(uId=uid).exists():
            messages.error(request, f"A patient with UID {uid} already exists.")
            return redirect('dashboard:patient-data')

        try:
            patient = Patient(
                owner=request.user,  # Set the owner
                name=name,
                age=age,
                sex=sex,
                uId=uid,
                email=email,
                address=address,
                phone=phone,
                picture=picture
            )
            patient.save()
            messages.success(request, "Patient details saved successfully!")
            return redirect('dashboard:patient-list')
        except IntegrityError as e:
            logger.error(f"Integrity error: {e}")
            messages.error(request, "A database integrity error occurred.")
            return redirect('dashboard:patient-data')
        except ValueError as e:
            logger.error(f"Value error: {e}")
            messages.error(request, "Invalid data provided.")
            return redirect('dashboard:patient-data')
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            messages.error(request, "An unexpected error occurred while saving the patient.")
            return redirect('dashboard:patient-data')

    return render(request, 'dashboard/add_patient.html')

@login_required
def patient_profile(request, patient_id):
    if request.user.is_superuser:
        patient = get_object_or_404(Patient, uId=patient_id)
    else:
        patient = get_object_or_404(Patient, uId=patient_id, owner=request.user)

    predictions = Prediction.objects.filter(patient=patient).order_by('-id')
    if predictions:
        latest = Prediction.objects.filter(patient=patient).latest('id')
        print(latest,"hello")
    else:
        latest = "none"
    
    for prediction in predictions:
        prediction.benign_count = Prediction.objects.filter(patient=patient, result='Benign').count()
        prediction.malignant_count = Prediction.objects.filter(patient=patient, result='Malignant').count()

    total_predictions = predictions.count()
    paginator = Paginator(predictions, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'patient': patient,
        'predictions': page_obj,  
        'total_predictions': total_predictions,
        "latest":latest,
    }
    return render(request, 'dashboard/patient_profile.html', context)

@login_required
def prediction_list(request):
    sort_by = request.GET.get('sort', 'id')
    order = request.GET.get('order', 'desc')

    if order == 'desc':
        sort_field = f'-{sort_by}'
    else:
        sort_field = sort_by

    if request.user.is_superuser:
        predictions = Prediction.objects.select_related('patient').order_by(sort_field)
    else:
        predictions = Prediction.objects.select_related('patient').filter(patient__owner=request.user).order_by(sort_field)

    paginator = Paginator(predictions, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'predictions': page_obj,
        'sort_by': sort_by,
        'order': order,
    }
    return render(request, 'dashboard/predictions_list.html', context)

def login_page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            messages.error(request,"User doesn't exist")
            return redirect("/login/")

        user = authenticate(username=username,password=password)

        if user is None:
            messages.error(request,"Invalid Password.")
            return redirect("/login/")
        else:
            login(request,user)
            messages.success(request,"Logged in successfully.")
            return redirect("/")
    if request.user.is_authenticated:
        messages.info(request,"User Logged Out.")
        logout(request)
    return render(request, "dashboard/login.html")

def logout_page(request):
    logout(request)
    messages.info(request,'Logout successful.')
    return redirect("/login/")

def register(request):
    if request.method == "POST":
        data = request.POST
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        username = data.get('username')
        password = data.get('password')
        verification_code = data.get('verification_code')

        if verification_code != 'astro-wiz':
            messages.error(request, "Invalid verification code.")
            return redirect('/register/')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('/register/')

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
        user.set_password(password)
        user.save()

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "User successfully created and logged in.")
            return redirect('/')
        else:
            messages.error(request, "Failed to log in after registration.")
            return redirect('/login/')

    return render(request, "dashboard/register.html")

@login_required
def patient_list(request):
    sort_by = request.GET.get('sort', 'uId')
    order = request.GET.get('order', 'asc')

    if order == 'desc':
        sort_field = f'-{sort_by}'
    else:
        sort_field = sort_by

    search_query = request.GET.get('search', '')

    # Admin can view all patients
    if request.user.is_superuser:
        patients = Patient.objects.all()
    else:
        patients = Patient.objects.filter(owner=request.user)

    if search_query:
        patients = patients.filter(name__icontains=search_query)

    patients = patients.order_by(sort_field)

    paginator = Paginator(patients, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'patients': page_obj,
        'sort_by': sort_by,
        'order': order,
        'search_query': search_query,
    }
    return render(request, 'dashboard/patient_list.html', context)

@login_required
def dashboard_home(request):
    # Check if the user is a superuser (admin)
    if request.user.is_superuser:
        # Admins can view all patients and predictions
        total_patients = Patient.objects.count()
        total_predictions = Prediction.objects.count()
        benign_count = Prediction.objects.filter(result='Benign').count()
        malignant_count = Prediction.objects.filter(result='Malignant').count()
    else:
        # Regular users can only view their own patients and predictions
        total_patients = Patient.objects.filter(owner=request.user).count()
        total_predictions = Prediction.objects.filter(patient__owner=request.user).count()
        benign_count = Prediction.objects.filter(patient__owner=request.user, result='Benign').count()
        malignant_count = Prediction.objects.filter(patient__owner=request.user, result='Malignant').count()

    context = {
        'total_patients': total_patients,
        'total_predictions': total_predictions,
        'benign_count': benign_count,
        'malignant_count': malignant_count,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def delete_prediction(request, prediction_id):
     try:
        #Admin can delete any patient.
        if request.user.is_superuser:
            prediction = get_object_or_404(Prediction, id=prediction_id)
        else:
            #Ensure that only patients created by loggedin user can be deleted
            prediction = get_object_or_404(Prediction, id=prediction_id, patient__owner=request.user)
            prediction.delete()
            messages.success(request, "Prediction deleted successfully.")
            return redirect(reverse('dashboard:prediction_list'))
        prediction.delete()
        messages.success(request, "Prediction deleted successfully.")
        return redirect(reverse('dashboard:prediction_list'))

     except Prediction.DoesNotExist:
        messages.error(request, "Prediction not found or unauthorized access.")
        return redirect('dashboard:prediction_list')
   

@login_required
def deletePrediction(request, prediction_id):
        #Admin can delete any patient.
    if request.user.is_superuser:
        prediction = get_object_or_404(Prediction, id=prediction_id)
    #Ensure that only patients created by loggedin user can be deleted
    else:
         prediction = get_object_or_404(Prediction, id=prediction_id, patient__owner=request.user)
    prediction.delete()
    messages.success(request, "Prediction deleted successfully.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def profile(request):
    return render(request, 'dashboard/index.html')

@login_required
def patient_data(request):
    return render(request, 'dashboard/add_patient.html')

@login_required
def delete(request, uId):
    if request.method == "POST":
        try:
            # Admin can delete any patient
            if request.user.is_superuser:
                 patient = get_object_or_404(Patient, uId=uId)
            else:
                 # Regular users can only delete their own patients
                 patient = get_object_or_404(Patient, uId=uId, owner=request.user)
            patient.delete()
            messages.success(request, f"Patient with ID {uId} deleted successfully.")
        except Patient.DoesNotExist:
            messages.error(request, "Patient not found or unauthorized access.")
        except Exception as e:
            messages.error(request, f"Failed to delete patient: {e}")
        return redirect("dashboard:patient-list")
    else:
        return redirect("dashboard:patient-list")

@login_required
def update(request, id):
    try:
        # Admin can update any patient
        if request.user.is_superuser:
            queryset = get_object_or_404(Patient, id=id)
        else:
            # Regular users can only update their own patients
            queryset = get_object_or_404(Patient, id=id, owner=request.user)

        if request.method == 'POST':
            data = request.POST
            name = data.get('name')
            age = data.get('age')
            uId = data.get('uId')
            email = data.get('email')
            address = data.get('address')
            picture = request.FILES.get('picture')
            phone = data.get('phone')
            sex = data.get('sex')

            queryset.name = name
            queryset.age = age
            queryset.sex = sex
            queryset.uId = uId
            queryset.email = email
            queryset.address = address
            queryset.phone = phone

            if picture:
                queryset.picture = picture

            queryset.save()
            messages.success(request, "Patient info Changed.")
            return redirect("dashboard:patient-list")

        context = {'patient': queryset}
        return render(request, "dashboard/update.html", context)

    except Patient.DoesNotExist:
        messages.error(request, "Patient not found or unauthorized access.")
        return redirect("dashboard:patient-list")


def modelinfo(request):

    model_info = {  
        "Model_Type": "Linear SVM",
        "Training_Accuracy": "95.12%",
        "Test_Accuracy": "94.82%",
        "Test_Precision": 0.92,  
        "Test_Recall": 0.99,      
        "Test_F1_Score": 0.95,    
        "Learning_Rate": 0.001,
        "Lambda_Parameter": 0.01,
        "Number_of_Iterations": 1000,
        "Image_Size": "(32, 32)",
        "Number_of_Features": 1024,
        "Number_of_Training_Samples": 10502,
        "Number_of_Testing_Samples": 2626,
        "Confusion_Matrix": [[1068, 123], [13, 1422]],
        "Data_Source": "DDSM Dataset", 
        "Number_of_Images": "13130", 
        "Benign_Count": "5000", 
        "Malignant_Count": "8130",
        "Image_Type": "Mammograms", 
        "Preprocessing_Steps": "Resized to 32x32 pixels, Converted to Grayscale"
    }

    context = {
        'model_info': model_info,
    }
    return render(request, "dashboard/modelinfo.html", context)