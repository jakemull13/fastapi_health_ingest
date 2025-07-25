# FastAPI Health Data Ingestion

This project provides a FastAPI backend for ingesting Apple Health workout and metric data. It supports ingestion into Google BigQuery and raw backup storage in GCS.

## 🚀 Endpoints

### `POST /upload/workouts`

Ingest workout and route data.

#### Example `curl`:

```bash
curl -X POST https://ingest-api-381855915236.us-central1.run.app/upload/workouts \
  -H "Content-Type: application/json" \
  -d @data/sample_workouts_real.json
```

### `POST /upload/metrics`

Ingest health metrics like heart rate, step count, etc.

#### Example `curl`:

```bash
curl -X POST https://ingest-api-381855915236.us-central1.run.app/upload/metrics \
  -H "Content-Type: application/json" \
  -d @data/sample_metrics.json
```

## 🧱 Deployment

### ⚙️ Setup GitHub Actions for Autodeploy

This project includes a GitHub Actions workflow that:
- Builds and pushes a Docker image to Google Artifact Registry
- Deploys the latest image to Cloud Run

## 🛠️ Setup Instructions

1. **Enable Cloud Run & Artifact Registry in GCP**
2. **Create GitHub secrets**:
   - `GCP_PROJECT`: `your-project`
   - `GCP_REGION`: `us-central1`
   - `GCP_SA_KEY`: Base64-encoded JSON service account key with deploy and artifact permissions

3. **Push to GitHub and GitHub Actions will deploy automatically.**

## 🐳 Local Development

```bash
uvicorn main:app --reload
```

## 🔒 Notes
- Replace `your-gcs-bucket-name` in `main.py` with your actual GCS bucket.
- Edit `.github/workflows/deploy.yml` for customization.

autoexport url/;
