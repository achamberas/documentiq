## Developing and Running Locally

Create a virtual environment
```
python3.9 -m venv venv
source venv/bin/activate
```

Install libraries
`pip install -r requirements.txt`

Run app `streamlit run <app_name>.py`

## Deploy to cloud run

1. Create the following secrets in Google Secret Manager:
    * OPENAI_API_KEY


2. Build the image

```
gcloud builds submit --tag us-east1-docker.pkg.dev/gristmill5/docker-images/mlflow
```

3. Deploy the built image to Cloud Run, updating variables below:

```
gcloud run deploy mlflow-test \
--image=us-east1-docker.pkg.dev/gristmill5/docker-images/mlflow \
--allow-unauthenticated \
--cpu=1 \
--memory=1Gi \
--cpu-throttling \
--platform=managed \
--region=us-east1 \
--project=gristmill5 \
--service-account=task-service-account@gristmill5.iam.gserviceaccount.com \
--set-env-vars "mlflow_db=mlflow" \
--set-env-vars "PG_CONN_NAME=gristmill5:us-east1:mlflow-test" \
--set-env-vars "ARTIFACTS_DESTINATION=gs://mlflow-artifacts-gm5" \
--update-secrets=mlflow_dbuser=mlflow_dbuser:1 \
--update-secrets=mlflow_dbpassword=mlflow_dbpassword:1
```

## Embedding into a web page

?embed=true&embed_options=hide_toolbar&embed_options=hide_padding&embed_options=hide_footer&embed_options=hide_colored_line&embed_options=disable_scrolling&sidebar=collapsed
