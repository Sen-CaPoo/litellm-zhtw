FROM ghcr.io/berriai/litellm:v1.94.0

COPY zhtw/ /zhtw/
RUN python /zhtw/patch_ui.py && rm -rf /zhtw
