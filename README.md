# DevWorkspaces

A comprehensive development workspace containing multiple projects including ML/DL dashboards, Django APIs, and DevOps tools.

## 📁 Project Structure

```
DevWorkspaces/
├── projects/                    # Main project applications
│   ├── yolov8-poc/             # YOLOv8 Object Detection Dashboard
│   │   ├── streamlit_yolov8_dashboard.py
│   │   ├── data.yaml
│   │   └── requirements.txt
│   ├── python-dashboard/        # Django REST API Dashboard
│   │   ├── manage.py
│   │   ├── python_dashboard/
│   │   └── requirements.txt
│   └── devops-dashboard/        # DevOps System Monitoring Dashboard
│       ├── devops_dashboard.sh
│       ├── devops_dashboard.ps1
│       ├── README.md
│       └── requirements.txt
├── infrastructure/              # Docker and Infrastructure configs
│   └── docker-compose.yml
├── scripts/                     # Utility and backup scripts
│   ├── backups/
│   │   ├── free_backup.py
│   │   ├── aws_s3_backup_setup.py
│   │   └── AWS_S3_BACKUP_SETUP_GUIDE.md
│   └── README.md
├── docs/                        # Documentation
│   ├── README_BACKUP.md
│   ├── timeline.txt
│   └── vscode_wsl_startup_log_summary.md
├── archive/                     # Large files and archives
└── TODO.md                      # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Git

### YOLOv8 Object Detection Dashboard
```bash
cd projects/yolov8-poc
pip install -r requirements.txt
streamlit run streamlit_yolov8_dashboard.py
```

### Django API Dashboard
```bash
cd projects/python-dashboard
python manage.py migrate
python manage.py runserver
```

### DevOps Dashboard
```bash
# Linux
cd projects/devops-dashboard
chmod +x devops_dashboard.sh
./devops_dashboard.sh

# Windows PowerShell
cd projects/devops-dashboard
.\devops_dashboard.ps1
```

### Using Docker
```bash
# Start all services
docker-compose up -d

# Services will be available at:
# - Django API: http://localhost:8000
# - DevOps Dashboard: http://localhost:3000
```

## 📦 Projects

### 1. YOLOv8 Object Detection POC
- Streamlit-based dashboard for YOLOv8 model training and inference
- Dataset analysis and configuration
- 3D reconstruction capabilities

### 2. Python Django Dashboard
- REST API built with Django
- Coding resources management
- Learning data fixtures

### 3. DevOps System Dashboard
- System monitoring utilities
- Multi-platform support (Windows/Linux)
- PowerShell and Shell script implementations

## 🛠️ Infrastructure

- **Docker Compose**: Orchestrates multiple services
- **Services**: django_api, backend, ml, dashboard
- **Port Mappings**: 8000, 8001, 8002, 3000

## 📝 Scripts & Utilities

### Backup Scripts
- `free_backup.py`: Free cloud backup solution
- `aws_s3_backup_setup.py`: AWS S3 backup configuration
- Support for GitHub, Google Drive, Hugging Face, Internet Archive

## 📄 Documentation

See `docs/` directory for:
- Backup strategies and guides
- Development timeline
- VSCode WSL startup notes

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 License

This project is for personal development and learning purposes.

## 🔗 References

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

