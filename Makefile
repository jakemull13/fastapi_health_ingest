
PROJECT_NAME=ingest-api
PORT=8080

build:
	docker build -t $(PROJECT_NAME):latest .

run:
	docker run -p $(PORT):8080 $(PROJECT_NAME):latest

test-workouts:
	curl -X POST http://localhost:$(PORT)/upload/workouts \
	  -H "Content-Type: application/json" \
	  --data-binary @sample_workouts.json

test-metrics:
	curl -X POST http://localhost:$(PORT)/upload/metrics \
	  -H "Content-Type: application/json" \
	  --data-binary @sample_metrics.json
