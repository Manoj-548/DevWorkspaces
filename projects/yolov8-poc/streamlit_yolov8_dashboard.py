import streamlit as st
import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from ultralytics import YOLO
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import hashlib
import uuid
import random

# Configuration constants
BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 0.001
IMG_SIZE = 640
MODEL_NAME = 'yolov8n.pt'
DATA_YAML = 'data.yaml'
CONFIDENCE_THRESHOLD = 0.5
NMS_IOU_THRESHOLD = 0.45

# Set page configuration
st.set_page_config(page_title="YOLOv8 POC Dashboard", page_icon="🔍", layout="wide", initial_sidebar_state="expanded")

# Title and description
st.title("🔍 YOLOv8 POC with 3D Reconstruction")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Getting Started", "System Info", "Dataset Analysis", "Configuration", "Training", "Inference", "Results"])

if page == "Getting Started":
    st.header("Getting Started with YOLOv8 POC")
    st.markdown("""
    This dashboard provides an interactive interface for training and using YOLOv8 models for object detection with 3D reconstruction capabilities.
    
    **Steps to use:**
    1. **Dataset Analysis**: Check your training and test datasets
    2. **Configuration**: Adjust training parameters as needed
    3. **Training**: Train the YOLOv8 model and 3D reconstruction model
    4. **Inference**: Run object detection on new images
    5. **Results**: View training and inference results
    """)

elif page == "System Info":
    st.header("System Information")
    st.write(f"PyTorch version: {torch.__version__}")
    st.write(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        st.write(f"CUDA device: {torch.cuda.get_device_name(0)}")
    st.write(f"Machine ID: {str(uuid.getnode())}")

elif page == "Dataset Analysis":
    st.header("Dataset Analysis")
    train_dir = "../train/images"
    test_dir = "../test/images"
    
    if os.path.exists(train_dir):
        train_images = [f for f in os.listdir(train_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        st.write(f"Training images: {len(train_images)}")
        if train_images:
            st.write("First 10 training images:")
            for img in train_images[:10]:
                st.write(f"- {img}")
            if len(train_images) > 10:
                st.write(f"... and {len(train_images) - 10} more")
    else:
        st.error(f"Training directory not found: {train_dir}")
    
    if os.path.exists(test_dir):
        test_images = [f for f in os.listdir(test_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        st.write(f"Test images: {len(test_images)}")
    else:
        st.error(f"Test directory not found: {test_dir}")
    
    if not train_images and not test_images:
        st.warning("No images found. Please add images to the train/images and test/images directories.")

elif page == "Configuration":
    st.header("Configuration")
    st.write("Adjust training parameters:")
    new_batch_size = st.slider("Batch Size", 1, 64, BATCH_SIZE)
    new_epochs = st.slider("Epochs", 1, 100, EPOCHS)
    new_lr = st.number_input("Learning Rate", value=LEARNING_RATE, format="%.6f")
    new_img_size = st.select_slider("Image Size", options=[320, 480, 640, 720, 960, 1280], value=IMG_SIZE)
    st.write(f"Configuration: batch_size={new_batch_size}, epochs={new_epochs}, lr={new_lr}, img_size={new_img_size}")

elif page == "Training":
    st.header("Model Training")
    st.write("Training parameters are configured in the Configuration section.")
    if st.button("Start Training"):
        st.info("Training started... (This would call the train functions)")
        # In a real implementation, this would call train_yolo_model() and train_3d_reconstruction()
        st.success("Training completed!")
    else:
        st.info("Click 'Start Training' to begin training the models.")

elif page == "Inference":
    st.header("Inference")
    st.write("Upload an image to run YOLOv8 object detection:")
    uploaded_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png', 'bmp'])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        if st.button("Run Inference"):
            st.info("Running inference... (This would call run_inference)")
            st.success("Inference completed!")

elif page == "Results":
    st.header("Results")
    st.write("Training and inference results will be displayed here.")
    st.info("Results will be available after training and inference are complete.")
