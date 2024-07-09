FROM python:3.10
WORKDIR /usr/src/app
COPY . .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
CMD ["python", "./common/main.py"]
# RUN ls
# CMD ["top"]
# EXPOSE 8994
# CMD ["ddtrace-run", "uvicorn", "--factory", "growth.main:create_app", "--host", "0.0.0.0", "--port", "8994"]