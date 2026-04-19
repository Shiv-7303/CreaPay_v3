export PYTHONPATH=$(pwd)
export FLASK_APP=run.py
export FLASK_ENV=development
export PRO_PLAN_PRICE=29900
flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1 &
