# YOLOv8 Object Detection POC

A Streamlit-based dashboard for YOLOv8 object detection model training and inference with 3D reconstruction capabilities.

## Features

- 📊 **Dataset Analysis**: Analyze training and test datasets
- ⚙️ **Configuration**: Adjust batch size, epochs, learning rate, image size
- 🏋️ **Training**: Train YOLOv8 models
- 🔍 **Inference**: Run object detection on uploaded images
- 📈 **Results**: View training and inference results

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run streamlit_yolov8_dashboard.py
```

## Configuration

Edit `data.yaml` to configure your dataset:

```yaml
path: .
train: train/images
val: test/images
nc: 1
names: ['object']
```

## Requirements

See `requirements.txt` for full dependency list.

