Create a virtual environment
```
python3.9 -m venv venv
source venv/bin/activate
```

Install libraries
`pip install -r requirements.txt`

Run app with `streamlit run <app_name>.py`

Push to Github for Streamlit Cloud to access latest version.

deploy to cloud run
```
docker build --tag app .
docker tag app us-east1-docker.pkg.dev/gristmill5/docker-images/app
docker push us-east1-docker.pkg.dev/gristmill5/docker-images/app
gcloud run deploy app \
--image=us-east1-docker.pkg.dev/gristmill5/docker-images/app:latest \
--allow-unauthenticated \
--cpu=1 \
--memory=4Gi \
--cpu-throttling \
--platform=managed \
--region=us-east1 \
--project=gristmill5
```

# Embedding

?embed=true&embed_options=hide_toolbar&embed_options=hide_padding&embed_options=hide_footer&embed_options=hide_colored_line&embed_options=disable_scrolling&sidebar=collapsed
