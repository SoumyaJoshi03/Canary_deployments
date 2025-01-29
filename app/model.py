import torch
from torchvision import models, transforms
from PIL import Image
import requests
from io import BytesIO
from prometheus_client import start_http_server, Summary, Gauge

# Start Prometheus metrics server on port 8001
start_http_server(8001)

# Define Prometheus metrics
model_accuracy = Gauge('model_accuracy', 'Model accuracy percentage')
model_latency_seconds_sum = Summary('model_latency_seconds_sum', 'Total latency in seconds')
model_latency_seconds_count = Summary('model_latency_seconds_count', 'Number of latency measurements')
http_requests_total = Gauge('http_requests_total', 'Total number of HTTP requests', ['version'])

class ImageClassifier:
    def __init__(self):
        # Load the pre-trained ResNet-50 model
        self.model = models.resnet50(pretrained=True)
        self.model.eval()
        
        # Define image transformations
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Load ImageNet class names
        with open("imagenet_classes.txt") as f:
            self.imagenet_classes = [line.strip() for line in f.readlines()]
        
        # Initialize metrics
        self.current_version = "v1"  # Update this when deploying a new model

    def predict(self, image_url: str):
        try:
            start_time = time.time()
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
            input_tensor = self.preprocess(image)
            input_batch = input_tensor.unsqueeze(0)  # Create a mini-batch as expected by the model
            
            with torch.no_grad():
                output = self.model(input_batch)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            confidence, predicted_idx = torch.max(probabilities, dim=0)
            prediction = self.imagenet_classes[predicted_idx]
            
            # Update metrics
            # For demonstration, assume accuracy is a fixed value. Replace with actual accuracy computation.
            model_accuracy.set(95.0)  # Example: 95% accuracy
            
            # Latency measurement
            latency = time.time() - start_time
            model_latency_seconds_sum.observe(latency)
            model_latency_seconds_count.observe(1)
            
            # Increment HTTP request count
            http_requests_total.labels(version=self.current_version).set(1)  # Example: Set to 1 per request
            
            return prediction, confidence.item()
        except Exception as e:
            # Handle exceptions and possibly update error metrics
            print(f"Prediction error: {e}")
            raise e