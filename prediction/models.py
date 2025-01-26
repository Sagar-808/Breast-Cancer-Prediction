from django.db import models
from dashboard.models import Patient  # Import the Patient model

class Prediction(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='predictions')  # Link to Patient
    uploaded_image = models.ImageField(upload_to='images/')
    processed_image = models.ImageField(upload_to='processed_images/', blank=True, null=True)  # Processed image field
    RESULT_CHOICES = [
        ('Benign', 'Benign'),
        ('Malignant', 'Malignant'),
    ]
    result = models.CharField(max_length=50, choices=RESULT_CHOICES, blank=True, null=True)  # Result will store "Malignant" or "Benign"

    def __str__(self):
        return f"{self.result} (Patient: {self.patient.name})" if self.result else f"Prediction for {self.patient.name}"

    @property
    def prediction_id(self):
        return self.id
