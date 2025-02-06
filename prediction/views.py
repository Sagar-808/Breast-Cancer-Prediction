import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Prediction, Patient
import joblib
from PIL import Image
import numpy as np
from django.core.serializers import serialize
from django.http import JsonResponse

# Load the trained SVM model
model_path = os.path.join(settings.BASE_DIR, 'prediction', 'svm_model.pkl')
clf = joblib.load(model_path)

@login_required
def predict_image(request, patient_id):
    # Fetch the patient
    if request.user.is_superuser:
         patient = get_object_or_404(Patient, uId=patient_id)
    else:
        patient = get_object_or_404(Patient, uId=patient_id, owner=request.user)

    if request.method == 'POST':
        uploaded_image = request.FILES.get('image')
        if uploaded_image:
            # Save the uploaded image and associate it with the patient
            prediction = Prediction.objects.create(uploaded_image=uploaded_image, patient=patient)

            # Process the uploaded image (resize, grayscale, etc.)
            img_path = prediction.uploaded_image.path
            img = Image.open(img_path).convert('L').resize((32, 32))
            img_array = np.array(img).flatten().reshape(1, -1)

            # Create the 'processed' directory if it doesn't exist
            processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
            os.makedirs(processed_dir, exist_ok=True)

            # Define the processed image path
            processed_img_name = os.path.basename(img_path)
            processed_img_path = os.path.join(processed_dir, processed_img_name)

            # Save the processed image
            img.save(processed_img_path)

            # Save the relative path of the processed image
            processed_img_relative_path = os.path.join('processed', processed_img_name)

            # Predict using the model
            result = clf.predict(img_array)

            # Map prediction to Malignant or Benign
            prediction.result = 'Malignant' if result[0] == 1 else 'Benign'
            prediction.processed_image = processed_img_relative_path
            prediction.save()

            # Show success message
            messages.success(request, f'Prediction complete: {prediction.result}')
            return redirect('prediction:result', prediction_id=prediction.id)

    return render(request, 'prediction/predict.html', {'patient': patient})

@login_required
def result(request, prediction_id):
    if request.user.is_superuser:
        # Admins can access any prediction
        prediction = get_object_or_404(Prediction, id=prediction_id)
    else:
    # Check if the user owns the Patient associated with the prediction
        prediction = get_object_or_404(Prediction, id=prediction_id, patient__owner=request.user)
    # Prepare the message based on the result
    if prediction.result == 'Malignant':
        prediction_message = "The model indicates a cancerous pattern. Further investigation, including biopsy and consultation with an oncologist, is strongly recommended to confirm the diagnosis and determine the appropriate treatment plan."
    else:
        prediction_message = "The model suggests a non-cancerous pattern. However, continued monitoring and follow-up appointments are advised to track any changes over time."
    # Get all previous predictions
    previous_predictions = Prediction.objects.filter(patient=prediction.patient).exclude(id=prediction_id).order_by('-id')

    # Determine medical progress
    medical_progress = None
    if previous_predictions:
        # Get the most recent previous prediction
        previous_prediction = previous_predictions.first()

        if prediction.result == 'Benign' and previous_prediction.result == 'Malignant':
            medical_progress = 'Improved'
        elif prediction.result == 'Malignant' and previous_prediction.result == 'Benign':
            medical_progress = 'Worsened'
        else:
            medical_progress = 'No Change'
    else:
        medical_progress = None  # For the first prediction

    # Prepare data for JavaScript
    benign_count = Prediction.objects.filter(patient=prediction.patient, result='Benign').count()
    malignant_count = Prediction.objects.filter(patient=prediction.patient, result='Malignant').count()

    if (benign_count + malignant_count) > 0:
        total = benign_count + malignant_count
    else:
        total = 1  # Prevent division by zero

    benign_percentage = (benign_count / total) * 100
    malignant_percentage = (malignant_count / total) * 100

    prediction_data = {
        'benign_count': benign_count,
        'malignant_count': malignant_count,
        'benign_percentage': benign_percentage,
        'malignant_percentage': malignant_percentage,
        'id': prediction.id,
    }

    return render(request, 'prediction/result.html', {
        'prediction': prediction,
        'message': prediction_message,
        'previous_predictions': previous_predictions,
        'medical_progress': medical_progress,
        'prediction_data': prediction_data,
    })
