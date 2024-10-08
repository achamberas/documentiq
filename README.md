## Developing and Running Locally

Create a virtual environment
```
python3.9 -m venv venv
source venv/bin/activate
python3.9 -m pip install --upgrade pip
```

Install libraries
`pip install -r requirements.txt`

Run app `streamlit run <app_name>.py`

## Deploy to cloud run

1. Create the following secrets in Google Secret Manager:
    * OPENAI_API_KEY
```
{
  "OPENAI_API_KEY": "PASSWORD_SECRET"
}
```

gcloud secrets create env-secrets \
    --replication-policy="automatic" \
    --data-file=env-secrets.json

and give permissions to service account

2. Build the image

```
gcloud builds submit --tag us-east1-docker.pkg.dev/gristmill5/docker-images/agentic
```

3. Deploy the built image to Cloud Run, updating variables below:

```
gcloud builds submit --tag us-east1-docker.pkg.dev/gristmill5/docker-images/agentic
gcloud run deploy agentic \
--image=us-east1-docker.pkg.dev/gristmill5/docker-images/agentic \
--allow-unauthenticated \
--cpu=1 \
--memory=1Gi \
--cpu-throttling \
--platform=managed \
--region=us-east1 \
--project=gristmill5 \
--service-account=bq-service-account@gristmill5.iam.gserviceaccount.com \
--set-env-vars=GOOGLE_AUTHORIZATION_URL="https://accounts.google.com/o/oauth2/auth",GOOGLE_TOKEN_URL="https://oauth2.googleapis.com/token",GOOGLE_REVOKE_TOKEN_URL="https://accounts.google.com/o/oauth2/revoke",REDIRECT_URI="https://agentic-365900802361.us-east1.run.app" \
--update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:1,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:1,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:1
```

## Embedding into a web page

?embed=true&embed_options=hide_toolbar&embed_options=hide_padding&embed_options=hide_footer&embed_options=hide_colored_line&embed_options=disable_scrolling&sidebar=collapsed
