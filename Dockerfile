FROM ghcr.io/berriai/litellm:v1.100.1

ARG LITELLM_UI_LANG=zh-TW
COPY zhtw/ /zhtw/
RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
