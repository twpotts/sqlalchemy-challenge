# Import the dependencies.

import datetime as dt
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker

#################################################
# Database Setup
#################################################


# reflect an existing database into a new model

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "Resources", "hawaii.sqlite")
sql_path = f'sqlite:///{db_path}'
engine = create_engine(sql_path)

# reflect the tables

Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table

station = Base.classes.station
measurement = Base.classes.measurement

# Create our session (link) from Python to the DB

Session = sessionmaker(bind=engine)
session = Session()

#################################################
# Flask Setup
#################################################

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = sql_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#################################################
# Flask Routes
#################################################

@app.route('/')
def list_routes():

    route_list = []
    for rule in app.url_map.iter_rules():
        route_list.append(rule.rule)
        
    return jsonify(route_list)

@app.route('/api/v1.0/precipitation')
def get_precipitation():

    most_recent_date = session\
        .query(func.max(measurement.date))\
        .first()
    
    twelve_months_back = (pd.to_datetime(most_recent_date[0]) - dt.timedelta(days=365)).strftime("%Y-%m-%d")
    
    data = session\
        .query(measurement.date, measurement.prcp)\
        .filter(measurement.date >= twelve_months_back)\
        .order_by(measurement.date)\
        .all()
    
    df = pd.DataFrame(data, columns=["date","prcp"])
    df = df.sort_values(by="date")
    records = df.to_dict('records')
    summary = dict(df["prcp"].describe())

    return jsonify(records)

@app.route('/api/v1.0/stations')
def get_stations():

    all_stations = session\
        .query(measurement.station)\
        .distinct()\
        .all()
        
    all_stations = [item[0] for item in all_stations]
    
    return jsonify(all_stations)

@app.route('/api/v1.0/tobs')
def get_tobs():

    station_counts = session\
        .query(measurement.station, func.count(measurement.id))\
        .group_by(measurement.station)\
        .order_by(func.count(measurement.id).desc())\
        .all()
    
    most_active_station_id = station_counts[0][0]

    most_recent_date2 = session\
        .query(func.max(measurement.date))\
        .filter(measurement.station == most_active_station_id)\
        .first()

    twelve_months_back2 = (pd.to_datetime(most_recent_date2[0]) - dt.timedelta(days=365)).strftime("%Y-%m-%d")

    station_data = session\
        .query(measurement.date, measurement.tobs)\
        .filter(measurement.station == most_active_station_id, measurement.date >= twelve_months_back2)\
        .all()
    
    tobs = [item[1] for item in station_data]
    
    return jsonify(tobs)

@app.route('/api/v1.0/<start>')
def get_start(start): # YYYY-MM-DD

    station_data = session\
        .query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs))\
        .filter(measurement.date >= start)\
        .all()
    
    summary = {
        "TMIN": station_data[0][0],
        "TAVG": station_data[0][2],
        "TMAX": station_data[0][1],
    }

    return jsonify(summary)

@app.route('/api/v1.0/<start>/<end>')
def get_start_end(start, end): # YYYY-MM-DD

    station_data = session\
        .query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs))\
        .filter(measurement.date >= start, measurement.date <= end)\
        .all()
    
    summary = {
        "TMIN": station_data[0][0],
        "TAVG": station_data[0][2],
        "TMAX": station_data[0][1],
    }

    return jsonify(summary)

if __name__ == "__main__":
    app.run(debug=True)