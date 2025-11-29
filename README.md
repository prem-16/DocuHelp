# DocuHelp -Smart Surgical Report Generator

AI-powered surgical video analysis and report generation system with human-in-the-loop feedback.

## Project Structure

```
surgical-report-generator/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── dataset/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── preprocessor.py
│   │   └── sop_parser.py
│   ├── vlm/
│   │   ├── __init__.py
│   │   ├── model.py
│   │   ├── inference.py
│   │   └── timestamp_extractor.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── frame_extractor.py
│   │   ├── annotation.py
│   │   └── segmentation.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── firebase_config.py
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── video.py
│   │           ├── feedback.py
│   │           └── report.py
│   ├── report/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── refiner.py
│   ├── testing/
│   │   ├── __init__.py
│   │   ├── validator.py
│   │   └── metrics.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── config.py
├── data/
│   ├── raw/
│   │   ├── videos/
│   │   └── sops/
│   ├── processed/
│   │   ├── frames/
│   │   └── annotations/
│   └── reports/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── firebase.js
│   │   └── App.js
│   └── package.json
├── tests/
│   ├── test_dataset.py
│   ├── test_vlm.py
│   ├── test_processing.py
│   └── test_report.py
├── scripts/
│   ├── setup_env.sh
│   └── download_models.py
├── notebooks/
│   └── exploration.ipynb
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── uv.lock
```

## Quick Start

### Prerequisites
- Python 3.11+
- uv package manager
- Firebase account (for UI)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/surgical-report-generator.git
cd surgical-report-generator
```

2. **Install uv** (if not installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Create virtual environment and install dependencies**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Download initial models**
```bash
python scripts/download_models.py
```

## Team Responsibilities

### Simon - Dataset & SOP Management
- **Module**: `src/dataset/`
- Curate 3-5 surgery categories with 1-2 videos each
- Create standardized SOP format
- Implement data loaders and preprocessors

### Anish - VLM Model Development
- **Module**: `src/vlm/`
- Build video understanding model
- Implement timestamp extraction
- Categorize SOP/non-SOP frames

### Prem - Frame Processing & Annotation
- **Module**: `src/processing/`
- Extract frames from video segments
- Generate annotations (bounding boxes, segmentation)
- Create processing pipeline

### Sanjeev - UI, Feedback & Report Generation
- **Module**: `src/ui/`, `src/report/`, `frontend/`
- Build Firebase-powered UI
- Implement feedback collection system
- Create report refinement workflow
- Generate final reports

## Development Workflow

### Running the Backend API
```bash
cd src/ui/api
uvicorn main:app --reload --port 8000
```

### Running the Frontend
```bash
cd frontend
npm install
npm start
```

### Running Tests
```bash
uv run pytest tests/ -v
```

### Data Pipeline Example
```bash
# Process a video
python -m src.vlm.inference --video data/raw/videos/surgery1.mp4 --sop data/raw/sops/category1.json

# Extract frames
python -m src.processing.frame_extractor --input data/raw/videos/surgery1.mp4 --output data/processed/frames/

# Generate report
python -m src.report.generator --input data/processed/ --output data/reports/
```

## Configuration

### Environment Variables
```bash
# .env
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_auth_domain
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_storage_bucket

# Model configs
VLM_MODEL_PATH=models/vlm/
SEGMENTATION_MODEL_PATH=models/segmentation/

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## Tech Stack

- **Package Management**: uv
- **Backend Framework**: FastAPI
- **VLM**: CLIP/BLIP-2/LLaVA (to be decided)
- **Video Processing**: OpenCV, FFmpeg
- **Segmentation**: SAM (Segment Anything Model)
- **UI Framework**: React + Firebase
- **Database**: Firebase Firestore
- **Testing**: pytest
- **CI/CD**: GitHub Actions

## Project Milestones

- [ ] **Week 1**: Dataset curation + initial VLM model
- [ ] **Week 2**: Frame processing pipeline + UI prototype
- [ ] **Week 3**: Feedback system + report generation
- [ ] **Week 4**: Testing agent + final integration

## Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firestore Database
3. Enable Storage for video/image uploads
4. Copy configuration to `.env`
5. Initialize Firebase in `frontend/src/firebase.js`

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Create Pull Request

## License

MIT License - see LICENSE file for details

## Contact

- Simon (Dataset): 
- Anish (VLM):
- Prem (Processing): 
- Sanjeev (UI/Reports): 