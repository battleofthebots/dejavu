# Base configuration used for all images - DO NOT CHANGE
FROM ghcr.io/battleofthebots/botb-base-image:ubuntu

# Add back vulnerable version
RUN apt-get update && \
    apt-get -y install exiftool
COPY ./DjVu.pm /usr/share/perl5/Image/ExifTool/DjVu.pm

WORKDIR /opt/
COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

USER user

COPY ./app.py app.py

ENV PORT=80

ENTRYPOINT python3 app.py -p $PORT
