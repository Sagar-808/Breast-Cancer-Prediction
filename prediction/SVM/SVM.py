import numpy as np
import pickle

class SVM:
    def __init__(self, iterations=1000, lr=0.01, lambdaa=0.01):
        self.lambdaa = lambdaa
        self.iterations = iterations
        self.lr = lr
        self.w = None
        self.b = None

    def initialize_parameters(self, X):
        """Initialize the parameters w and b."""
        m, n = X.shape
        self.w = np.zeros(n)
        self.b = 0

    def gradient_descent(self, X, y):
        """Run gradient descent to optimize w and b."""
        y_ = np.where(y <= 0, -1, 1)
        for i, x in enumerate(X):
            if y_[i] * (np.dot(x, self.w) - self.b) >= 1:
                dw = 2 * self.lambdaa * self.w
                db = 0
            else:
                dw = 2 * self.lambdaa * self.w - np.dot(x, y_[i])
                db = y_[i]
            self.update_parameters(dw, db)

    def update_parameters(self, dw, db):
        """Update w and b based on the gradients."""
        self.w = self.w - self.lr * dw
        self.b = self.b - self.lr * db

    def fit(self, X, y):
        """Train the model using gradient descent."""
        self.initialize_parameters(X)
        for i in range(self.iterations):
            self.gradient_descent(X, y)

    def predict(self, X):
        """Predict labels using the trained SVM model."""
        output = np.dot(X, self.w) - self.b
        label_signs = np.sign(output)
        predictions = np.where(label_signs <= -1, 0, 1)  # 0 for class 0, 1 for class 1
        return predictions

    def save_model(self, filename):
        """Save the trained model to a file."""
        model_data = {
            "lambdaa": self.lambdaa,
            "learning_rate": self.lr,
            "W": self.w,
            "b": self.b,
        }
        with open(filename, "wb") as file:
            pickle.dump(model_data, file)

    @classmethod
    def load_model(cls, filename):
        """Load the trained model from a file."""
        with open(filename, "rb") as file:
            model_data = pickle.load(file)
        
        # Create an instance of the SVM class and load the parameters
        loaded_model = cls(
            lr=model_data["learning_rate"], lambdaa=model_data["lambdaa"]
        )
        loaded_model.w = model_data["W"]
        loaded_model.b = model_data["b"]
        
        return loaded_model