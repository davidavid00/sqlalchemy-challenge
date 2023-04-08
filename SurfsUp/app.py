import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import date, timedelta
import pandas as pd

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine,reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Part 1
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start> and /api/v1.0/<start>/<end><br/>"
    )

# Part 2
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create link from Python to the DB
    session = Session(engine)

    # Query all the data
    results = session.query(Measurement.date, Measurement.prcp).all()
    
    session.close()

    # Convert list of tuples into normal list
    precip_by_date = {}
    for date, prcp in results:
        if date in precip_by_date:
            precip_by_date[date].append(prcp)
        else:
            precip_by_date[date] = [prcp]

    # Create a list of dictionaries with date and precipitation for each date
    record_list = []
    for date, prcp_list in precip_by_date.items():
        record_dict = {date: prcp_list}
        record_list.append(record_dict)


    return jsonify(record_list)


# Part 3
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all stations
    results = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_stations
    all_stations = []
    for record in results:
        station_dict = {
        "id": record.id,
        "station": record.station,
        "name": record.name,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "elevation": record.elevation
        }
        all_stations.append(station_dict)
    return jsonify(all_stations)


# Part 4
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    # Calculate the date range for the previous year
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        filter(Measurement.date >= '2016-08-18').\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]
    
    # Query the temperature observations for the previous year for the most active station
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= '2016-08-18').all()

    # Convert the results to a JSON list
    temperature_data = [{'date': str(date), 'temperature': temperature} for date, temperature in results]
    return jsonify(temperature_data)


# Part 5
def calculate_temperatures(start_date, end_date=None):

    session = Session(engine)
    
    # Filter the data based on the specified date range
    if end_date:
        filtered_data = session.query(
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")
        ).filter(
            Measurement.date >= start_date,
            Measurement.date <= end_date
        ).one()
    else:
        filtered_data = session.query(
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")
        ).filter(
            Measurement.date >= start_date
        ).one()
    # Return the results as a dictionary
    return {"TMIN": filtered_data.TMIN, "TAVG": filtered_data.TAVG, "TMAX": filtered_data.TMAX}

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def date_specified(start, end=None):
    # calculate TMIN, TAVG, and TMAX for the specified date range
    result = calculate_temperatures(start, end)
    # return the result as a JSON response
    return jsonify(result)



if __name__ == '__main__':
    app.run(debug=True)
