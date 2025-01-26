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
        # Debugging input data
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)

        # Extract form data
        name = request.POST.get('name')
        uid = request.POST.get('uId')  # Corrected field name
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        picture = request.FILES.get('picture')

        print(f"Extracted data - Name: {name}, UID: {uid}, Email: {email}, Address: {address}, Phone: {phone}")

        # Check for duplicate UID
        if Patient.objects.filter(uId=uid).exists():
            messages.error(request, f"A patient with UID {uid} already exists.")
            print("Duplicate UID detected.")
            return redirect('dashboard:patient-data')

        # Save new patient to database
        try:
            patient = Patient(
                name=name,
                uId=uid,
                email=email,
                address=address,
                phone=phone,
                picture=picture
            )
            patient.save()
            print(f"Patient saved successfully: {patient}")
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
    # Fetch patient details
    patient = Patient.objects.get(uId=patient_id)
    predictions = Prediction.objects.filter(patient=patient).order_by('-id')

    # Add pagination
    paginator = Paginator(predictions, 5)  # 4 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'patient': patient,
        'predictions': page_obj,  # Pass the page object instead of the full list
    }
    return render(request, 'dashboard/patient_profile.html', context)
@login_required
def prediction_list(request):
    # Get sorting field and direction from request
    sort_by = request.GET.get('sort', 'id')  # Default sorting by 'id'
    order = request.GET.get('order', 'desc')  # Default order is 'desc'

    # Adjust sorting order
    if order == 'desc':
        sort_field = f'-{sort_by}'
    else:
        sort_field = sort_by

    # Query predictions with related patient data
    predictions = Prediction.objects.select_related('patient').all().order_by(sort_field)

    # Paginate predictions
    paginator = Paginator(predictions, 7)  # 10 items per page
    page_number = request.GET.get('page')  # Current page
    page_obj = paginator.get_page(page_number)

    context = {
        'predictions': page_obj,  # Paginated predictions
        'sort_by': sort_by,  # Pass the current sorting field to template
        'order': order,  # Pass the current sorting order to template
    }
    return render(request, 'dashboard/predictions_list.html', context)

# def prediction_list(request):
#     predictions = Prediction.objects.all().order_by('-id')  # Fetch all predictions, newest first
#     paginator = Paginator(predictions, 7)  
#     page_number = request.GET.get('page')  # Get the current page number
#     page_obj = paginator.get_page(page_number)  # Get the predictions for the current page

#     context = {
#         'predictions': page_obj,  # Pass the paginated predictions
#     }
#     return render(request, 'dashboard/predictions_list.html', context)

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
            return redirect("/")  # Redirect to home or dashboard
        
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
        
        if User.objects.filter(username=username).exists():
            messages.error(request,"Username already taken.")
            return redirect('/register/')
        
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
        user.set_password(password)
        user.save()

        messages.success(request,"User successfully created.")
        return redirect('/login/')  # Redirect to login after successful registration

    if request.user.is_authenticated:
        messages.info(request,"User Logged Out.")
        logout(request)
    return render(request, "dashboard/register.html")


###################################################

@login_required
def patient_list(request):
    # Get sorting field and direction from request
    sort_by = request.GET.get('sort', 'uId')  # Default sorting by 'uId'
    order = request.GET.get('order', 'asc')  # Default order is 'asc'

    # Adjust sorting order
    if order == 'desc':
        sort_field = f'-{sort_by}'
    else:
        sort_field = sort_by

    # Filter patients by search query
    search_query = request.GET.get('search', '')  # Get search query
    patients = Patient.objects.all()
    if search_query:
        patients = patients.filter(name__icontains=search_query)

    # Sort the filtered patients
    patients = patients.order_by(sort_field)

    # Paginate patients
    paginator = Paginator(patients, 5)  
    page_number = request.GET.get('page')  # Current page
    page_obj = paginator.get_page(page_number)

    context = {
        'patients': page_obj,  # Paginated patients
        'sort_by': sort_by,  # Current sorting field
        'order': order,  # Current sorting order
        'search_query': search_query,  # Current search query
    }
    return render(request, 'dashboard/patient_list.html', context)
# def patient_list(request):
    patients = Patient.objects.all()
    if request.GET.get('search'):
        queryset = queryset.filter(name__icontains = request.GET.get('search'))
    
    return render(request, 'dashboard/patient_list.html',{'patients': patients})


def dashboard_home(request):
    # Calculate statistics
    total_patients = Patient.objects.count()
    total_predictions = Prediction.objects.count()
    benign_count = Prediction.objects.filter(result='Benign').count()
    malignant_count = Prediction.objects.filter(result='Malignant').count()

    context = {
        'total_patients': total_patients,
        'total_predictions': total_predictions,
        'benign_count': benign_count,
        'malignant_count': malignant_count,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def delete_prediction(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    prediction.delete()
    messages.success(request, "Prediction deleted successfully.")
    return redirect(reverse('dashboard:prediction_list'))

@login_required
def deletePrediction(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    prediction.delete()
    messages.success(request, "Prediction deleted successfully.")
    return 
@login_required
def profile(request):
    return render(request, 'dashboard/index.html')

@login_required
def patient_data(request):
    return render(request, 'dashboard/add_patient.html')

############################################################

@login_required
def delete(request, uId):
    # Ensure the request is valid and includes the user context
    if request.method == "POST":  # Confirm the delete action is via POST for safety
        # Get the object or return a 404 if it doesn't exist
        patient = get_object_or_404(Patient, uId=uId)
        # Delete the patient record
        patient.delete()
        # Redirect to the patients list page
        return redirect("dashboard:patient-list")  # Use your named URL
    else:
        # Return a 405 Method Not Allowed for non-POST requests
        return redirect("dashboard:patient-list")




@login_required
def update(request, id):
    queryset = Patient.objects.get(id=id)
    if request.method == 'POST':
        data = request.POST
        name = data.get('name')
        uId = data.get('uId')
        email = data.get('email')
        address = data.get('address')
        picture = request.FILES.get('picture')
        phone = data.get('phone')
        
        queryset.name = name
        queryset.uId = uId
        queryset.email = email
        queryset.address = address
        queryset.phone = phone
        
        if picture:
            queryset.picture = picture
            
        queryset.save()
        messages.success(request, "Patient info Changed.")
        return redirect("/patients/")
        
    context = {'patient': queryset}
    return render(request, "dashboard/update.html", context)


