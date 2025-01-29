import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Prediction, Patient
import joblib
from PIL import Image
import numpy as np

# Load the trained SVM model
model_path = os.path.join(settings.BASE_DIR, 'prediction', 'svm_model.pkl')
clf = joblib.load(model_path)

@login_required
def predict_image(request, patient_id):
    # Fetch the patient using patient_id
    patient = get_object_or_404(Patient, uId=patient_id)

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
    # Fetch the prediction instance
    prediction = get_object_or_404(Prediction, id=prediction_id)

    # Prepare the message based on the result
    if prediction.result == 'Malignant':
        prediction_message = "Please consult with your doctor for further evaluation and treatment options."
    else:
        prediction_message = "No immediate concern, but recommended regular monitoring for any changes."

    return render(request, 'prediction/result.html', {
        'prediction': prediction,
        'message': prediction_message,
    })
