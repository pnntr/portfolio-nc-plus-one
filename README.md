# README
> Portfolio NC one project for event browsing, organising, RSVPing and more

## Setup
### Requirements
- Python 3.13.15
- psql (PostgreSQL) 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)

### Install
1. clone repo and cd into it
2. install python env
```bash
python -m venv venv
source venv/bin/activate
```
3. install python deps
```bash
pip install -r requirements.txt
```
4. create and seed the database, run:
```
psql -f db/setup.sql
python db/utils.py
```

### Running app
1. start server
```bash
uvicorn main:app --reload
```
2. see endpoints
- in your browser go to "localhost:8000/docs"

### Testing
1. run tests
```bash
pytest
```
2. optional: for verbose test output run
```bash
pytest -vvv
```
