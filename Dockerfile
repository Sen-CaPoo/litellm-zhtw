FROM ghcr.io/berriai/litellm:v1.93.0

COPY zhtw/ /zhtw/
RUN python /zhtw/patch_ui.py && rm -rf /zhtw
