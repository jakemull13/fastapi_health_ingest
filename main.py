from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from google.cloud import bigquery, storage
from datetime import datetime
import json
import uuid

app = FastAPI()

# GCP Configuration
PROJECT_ID = "jake-mullins-portfolio"
BQ_DATASET = "personal_health"
BQ_WORKOUTS_TABLE = "raw_workouts"
BQ_ROUTES_TABLE = "raw_workout_routes"
BQ_METRICS_TABLE = "raw_metrics"
GCS_BUCKET = "your-gcs-bucket-name"
UPLOAD_RAW_TO_GCS = False

# GCP Clients
bq_client = bigquery.Client(project=PROJECT_ID)
gcs_client = storage.Client(project=PROJECT_ID)

# GCS upload
def upload_raw_to_gcs(data: List[dict], prefix: str) -> str:
    blob_name = f"{prefix}/raw_{datetime.utcnow().isoformat()}_{uuid.uuid4().hex}.json"
    blob = gcs_client.bucket(GCS_BUCKET).blob(blob_name)
    blob.upload_from_string(json.dumps(data, indent=2), content_type="application/json")
    return f"gs://{GCS_BUCKET}/{blob_name}"

# BigQuery insert helpers
def insert_workouts_bq(workouts: List[dict]):
    rows = [{
        "workout_id": w.get("id"),
        "name": w.get("name"),
        "start": w.get("start"),
        "end": w.get("end"),
        "duration": w.get("duration"),
        "active_energy_burned": w.get("activeEnergyBurned", {}).get("qty"),
        "raw_json": json.dumps(w)
    } for w in workouts]
    bq_client.insert_rows_json(f"{PROJECT_ID}.{BQ_DATASET}.{BQ_WORKOUTS_TABLE}", rows)

def insert_routes_bq(workouts: List[dict]):
    rows = []
    for w in workouts:
        if w.get("route"):
            for p in w.get("route", []):
                rows.append({
                    "workout_id": w.get("id"),
                    "timestamp": p.get("timestamp"),
                    "latitude": p.get("latitude"),
                    "longitude": p.get("longitude"),
                    "altitude": p.get("altitude"),
                    "speed": p.get("speed"),
                    "course": p.get("course")
                })
    if rows:
        bq_client.insert_rows_json(f"{PROJECT_ID}.{BQ_DATASET}.{BQ_ROUTES_TABLE}", rows)

def insert_metrics_bq(metrics: List[dict]):
    rows = [{
        "type": m.get("type"),
        "unit": m.get("unit"),
        "date": m.get("date"),
        "value": m.get("value"),
        "raw_json": json.dumps(m)
    } for m in metrics]
    bq_client.insert_rows_json(f"{PROJECT_ID}.{BQ_DATASET}.{BQ_METRICS_TABLE}", rows)

# Create BigQuery tables
def create_bigquery_tables():
    dataset_ref = bq_client.dataset(BQ_DATASET)
    try: bq_client.get_dataset(dataset_ref)
    except: bq_client.create_dataset(bigquery.Dataset(dataset_ref))

    def create_table_if_missing(name, schema):
        table_ref = dataset_ref.table(name)
        try: bq_client.get_table(table_ref)
        except: bq_client.create_table(bigquery.Table(table_ref, schema=schema))

    create_table_if_missing(BQ_WORKOUTS_TABLE, [
        bigquery.SchemaField("workout_id", "STRING"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("start", "TIMESTAMP"),
        bigquery.SchemaField("end", "TIMESTAMP"),
        bigquery.SchemaField("duration", "FLOAT"),
        bigquery.SchemaField("active_energy_burned", "FLOAT"),
        bigquery.SchemaField("raw_json", "STRING"),
    ])
    create_table_if_missing(BQ_ROUTES_TABLE, [
        bigquery.SchemaField("workout_id", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("latitude", "FLOAT"),
        bigquery.SchemaField("longitude", "FLOAT"),
        bigquery.SchemaField("altitude", "FLOAT"),
        bigquery.SchemaField("speed", "FLOAT"),
        bigquery.SchemaField("course", "FLOAT"),
    ])
    create_table_if_missing(BQ_METRICS_TABLE, [
        bigquery.SchemaField("type", "STRING"),
        bigquery.SchemaField("unit", "STRING"),
        bigquery.SchemaField("date", "TIMESTAMP"),
        bigquery.SchemaField("value", "FLOAT"),
        bigquery.SchemaField("raw_json", "STRING"),
    ])

create_bigquery_tables()

# Pydantic models
class QuantityUnit(BaseModel):
    qty: Optional[float]
    units: Optional[str]

class RoutePoint(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    altitude: Optional[float]
    speed: Optional[float]
    course: Optional[float]

class Workout(BaseModel):
    id: str
    name: Optional[str]
    start: Optional[str]
    end: Optional[str]
    duration: Optional[float]
    activeEnergyBurned: Optional[QuantityUnit]
    route: Optional[List[RoutePoint]] = None 

class Metric(BaseModel):
    type: str
    unit: Optional[str]
    date: str
    value: float

class UploadWorkoutsRequest(BaseModel):
    data: Dict[str, List[Workout]]

class UploadMetricsRequest(BaseModel):
    data: Dict[str, List[Metric]]

# Endpoints
@app.post("/upload/workouts")
async def upload_workouts(req: UploadWorkoutsRequest):
    try:
        workouts = [w.dict() for w in req.data.get("workouts", [])]
        if not workouts:
            return {"message": "No workouts provided"}
        insert_workouts_bq(workouts)
        insert_routes_bq(workouts)
        gcs_url = upload_raw_to_gcs(workouts, "workouts") if UPLOAD_RAW_TO_GCS else None
        return {"message": f"{len(workouts)} workouts stored", "gcs_backup": gcs_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/metrics")
async def upload_metrics(req: UploadMetricsRequest):
    try:
        metrics = [m.dict() for m in req.data.get("metrics", [])]
        if not metrics:
            return {"message": "No metrics provided"}
        insert_metrics_bq(metrics)
        gcs_url = upload_raw_to_gcs(metrics, "metrics") if UPLOAD_RAW_TO_GCS else None
        return {"message": f"{len(metrics)} metrics stored", "gcs_backup": gcs_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    create_bigquery_tables()
    app.run(debug=True)

