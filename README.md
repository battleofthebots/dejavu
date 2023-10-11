# DejaVu

This container runs a web application that analyzes images and returns their metadata using exiftool. Users send the application a URL to an image and the app will retrieve it, analyze it, and return the results. The version of exiftool used by the application is vulnerable to CVE-2021-22204 as the DjVu file module has an unsafe eval which can be triggered with a specially crafted file to execute arbitrary commands. Competitors must use their bot to host a malicious "image" (as a png/jpeg/tiff), then tell the app to request their malicious image and evaluate it resulting in their payload executing.

## Building
```sh
docker build . -t dejavu
```

## Running
```sh
docker run --cpus=1 -p 8000:80 dejavu
```

## Exploiting
```sh
python3 dejavu.py <container addr> <lhost address> --lhost <lhost address>
```
> **NOTE**
> It is very unstable

> **NOTE**
> The `requirements.txt` is only for the same python running on the base image. If on a different system or python version, just manually install the python packages.

## References 
* [a-case-study-on-cve-2021-22204-exiftool-rce](https://blog.convisoappsec.com/en/a-case-study-on-cve-2021-22204-exiftool-rce/)
