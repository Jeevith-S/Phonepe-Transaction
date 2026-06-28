from fastapi import FastAPI, UploadFile, File
from PIL import Image
from dotenv import load_dotenv
import os
import io
import cv2
import base64
from io import BytesIO
import torch
import torch.nn as nn
from torchvision import models, transforms
import numpy as np

import google.generativeai as genai
load_dotenv()

# ==========================================================
# GEMINI API
# ==========================================================

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

llm = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# ==========================================================
# FASTAPI APP
# ==========================================================

app = FastAPI(
    title="Chest X-ray AI API"
)

# ==========================================================
# DISEASE LABELS
# ==========================================================

disease_cols = [

    'Atelectasis',
    'Cardiomegaly',
    'Consolidation',
    'Edema',
    'Effusion',
    'Emphysema',
    'Fibrosis',
    'Hernia',
    'Infiltration',
    'Mass',
    'No Finding',
    'Nodule',
    'Pleural_Thickening',
    'Pneumonia',
    'Pneumothorax'
]

# ==========================================================
# DEVICE
# ==========================================================

device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

print("Using Device:", device)

# ==========================================================
# LOAD MODEL
# ==========================================================

model = models.resnet18(
    weights=None
)

num_features = model.fc.in_features

model.fc = nn.Linear(
    num_features,
    len(disease_cols)
)

model.load_state_dict(
    torch.load(
        "best_resnet18.pth",
        map_location=device
    )
)

model = model.to(device)

model.eval()

print("✅ Model Loaded")

# ==========================================================
# IMAGE TRANSFORM
# ==========================================================

transform = transforms.Compose([

    transforms.Resize((224,224)),

    transforms.ToTensor(),

    transforms.Normalize(

        mean=[0.485,0.456,0.406],

        std=[0.229,0.224,0.225]
    )
])
# ==========================================================
# GRAD CAM FUNCTION
# ==========================================================

def generate_gradcam(model, image_tensor):

    gradients = []
    activations = []

    def forward_hook(module, input, output):
        activations.append(output)

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0])

    target_layer = model.layer4[-1]

    fh = target_layer.register_forward_hook(
        forward_hook
    )

    bh = target_layer.register_full_backward_hook(
        backward_hook
    )

    output = model(image_tensor)

    pred_class = output.argmax()

    model.zero_grad()

    output[0, pred_class].backward()

    grads = gradients[0][0].cpu().detach().numpy()

    acts = activations[0][0].cpu().detach().numpy()

    weights = np.mean(
        grads,
        axis=(1, 2)
    )

    cam = np.zeros(
        acts.shape[1:],
        dtype=np.float32
    )

    for i, w in enumerate(weights):

        cam += w * acts[i]

    cam = np.maximum(cam, 0)

    cam = cv2.resize(
        cam,
        (224, 224)
    )

    cam = cam - np.min(cam)

    cam = cam / np.max(cam)

    heatmap = np.uint8(255 * cam)

    heatmap = cv2.applyColorMap(
        heatmap,
        cv2.COLORMAP_JET
    )

    heatmap = cv2.cvtColor(
        heatmap,
        cv2.COLOR_BGR2RGB
    )

    fh.remove()
    bh.remove()

    return heatmap
# ==========================================================
# HOME ROUTE
# ==========================================================

@app.get("/")
def home():

    return {
        "message":
        "Chest X-ray API Running Successfully"
    }

# ==========================================================
# PREDICT ROUTE
# ==========================================================

@app.post("/predict")
async def predict(
        file: UploadFile = File(...)
):

    # Read uploaded image

    contents = await file.read()

    image = Image.open(
        io.BytesIO(contents)
    ).convert("RGB")

    # Preprocess

    img = transform(image)

    img = img.unsqueeze(0)

    img = img.to(device)

    # Prediction

    with torch.no_grad():

        outputs = model(img)

        probs = torch.sigmoid(
            outputs
        ).cpu().numpy()[0]

    threshold = 0.15

    predicted_diseases = []

    for i, disease in enumerate(
            disease_cols
    ):

        if probs[i] > threshold:

            predicted_diseases.append(
                disease
            )

    if len(predicted_diseases) == 0:

        predicted_diseases = [
            "No Disease Detected"
        ]

    probabilities = {}

    for i, disease in enumerate(
            disease_cols
    ):

        probabilities[disease] = round(
            float(probs[i]),
            4
        )

    # ======================================================
    # GEMINI EXPLANATION
    # ======================================================

    prompt = f"""
    You are an expert radiology assistant.

    Predicted diseases:

    {predicted_diseases}

    Explain in simple language:

    1. Disease overview
    2. Common symptoms
    3. Causes
    4. Treatments
    5. Prevention

    Mention clearly that this is not
    a final medical diagnosis.
    """

    response = llm.generate_content(
        prompt
    )

    explanation = response.text
    # ======================================================
# GENERATE GRAD CAM
# ======================================================

heatmap = generate_gradcam(
    model,
    img
)

heatmap = Image.fromarray(
    heatmap
)

buffer = BytesIO()

heatmap.save(
    buffer,
    format="PNG"
)

gradcam = base64.b64encode(
    buffer.getvalue()
).decode()

    # ======================================================
    # RETURN JSON
    # ======================================================

    return {

        "predicted_diseases":
            predicted_diseases,

        "probabilities":
            probabilities,

        "explanation":
            explanation,
        "gradcam":
            gradcam    

    }