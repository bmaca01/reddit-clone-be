#!/usr/bin/env bash

./create_db.sh

gunicorn --threads 4 -b 0.0.0.0:8080 'flaskr:create_app()' 
