#!/bin/bash

export DASHSCOPE_API_KEY="sk-4789ed940645494a973deeb7a50447a9"

gunicorn --bind 0.0.0.0:8000 app:app