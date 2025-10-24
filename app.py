from flask import Flask, request, jsonify, render_template
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from models import IngestPayload
from config import settings
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

client = InfluxDBClient(url=settings.INFLUX_URL, token=settings.INFLUX_TOKEN, org=settings.INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()
local_tz = pytz.timezone("America/Bogota") 

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/ingest', methods=['POST'])
def ingest():
    try:
        data = request.get_json(force=True)
        payload = IngestPayload.model_validate(data)

        p = (
        Point("condensation_risk")
        .tag("source", payload.source or "device")
        .field("temperature_c", float(payload.temp_c))
        .field("humidity_pct", float(payload.humidity))
        .field("accel_x_g", float(payload.acc_x))
        .field("accel_y_g", float(payload.acc_y))
        .field("accel_z_g", float(payload.acc_z))
        .field("prediction", float(payload.prediction))
        .time(payload.timestamp, WritePrecision.NS)
        )
        write_api.write(bucket=settings.INFLUX_BUCKET, org=settings.INFLUX_ORG, record=p)
        return jsonify({"message": "ingested", "bucket": settings.INFLUX_BUCKET, "org": settings.INFLUX_ORG}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def dashboard():
    now = datetime.utcnow()
    start = now - timedelta(hours=24)
    stop = now + timedelta(hours=24)


    flux = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
    |> range(start: {start.isoformat()}Z, stop: {stop.isoformat()}Z)
    |> filter(fn: (r) => r["_measurement"] == "condensation_risk")
    |> filter(fn: (r) => r["_field"] == "temperature_c" or r["_field"] == "humidity_pct" or r["_field"] == "prediction" or r["_field"] == "accel_x_g" or r["_field"] == "accel_y_g" or r["_field"] == "accel_z_g")
    |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
    |> yield(name: "last")
    '''


    tables = query_api.query(flux)

    print(tables)
    rows = {}
    for table in tables:
        for record in table.records:
            t = record.get_time()
            local_time = t.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S")
            iso = t.isoformat()
            if iso not in rows:
                rows[iso] = {"time": local_time, "source": record.values.get("source") or rows.get(iso, {}).get("source")}
            rows[iso][record.get_field()] = record.get_value()
    
            src = record.values.get("source")
            if src:
                rows[iso]["source"] = src


    data = sorted(rows.values(), key=lambda x: x["time"], reverse=True)


    latest = data[0] if data else None
    status = None
    if latest:
        pred = latest.get("prediction", 0)
        status = "ALERTA (riesgo)" if pred and float(pred) >= 0.3 else "OK"

    return render_template('dashboard.html', data=data[:100], status=status, latest=latest)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)