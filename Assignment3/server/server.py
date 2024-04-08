from flask import Flask, jsonify, request
import os
from manager import Manager
import json
import requests

app = Flask(__name__)
managers = {}


def appendEntry(endpoint, method, payload):
    logs = open("logs", "a")
    logs.write(
        json.dumps({"endpoint": endpoint, "method": method, "payload": payload}) + "\n"
    )
    logs.close()


def executeLog(logRequests):
    methods_mapping = {
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
    }

    for req in logRequests:
        reqJson = json.loads(req)
        endpoint = reqJson["endpoint"]
        method = reqJson["method"]
        payload = reqJson["payload"]
        methods_mapping[method](f"http://localhost:5000/{endpoint}", json=payload)


@app.route("/config", methods=["POST"])
def config():
    payload = request.json
    logRequests = payload.get("logRequests", [])
    message = ""
    for shardName in payload["shards"]:
        try:
            managers[shardName] = Manager(
                shardName, payload["schema"]["columns"], payload["schema"]["dtypes"]
            )
            message += f"Server0: {shardName}, "
        except Exception as e:
            print(e)
    executeLog(logRequests)
    message += "configured"
    response = {"message": message, "status": "successful"}
    return response, 200


@app.route("/copy", methods=["GET"])
def copy():
    payload = request.json
    message = []
    for shardName in payload["shards"]:
        message.extend(managers[shardName].copy())
    response = {"message": message, "status": "success"}
    return response, 200


@app.route("/read", methods=["GET"])
def read():
    payload = request.json
    shardName = payload["shard"]
    Stud_id_range = payload["Stud_id"]
    data = managers[shardName].read(Stud_id_range["low"], Stud_id_range["high"])
    response = {"data": data, "status": "success"}
    return response, 200


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    return jsonify({}), 200


@app.route("/write", methods=["POST"])
def write():
    payload = request.json
    shardName = payload["shard"]
    entries = payload["data"]
    appendEntry(request.endpoint, request.method, payload)
    current_idx = managers[shardName].write(entries)
    response = {
        "message": "Data entries added",
        "current_idx": current_idx,
        "status": "success",
    }
    return response, 200


@app.route("/update", methods=["PUT"])
def update():
    payload = request.json
    shardName = payload["shard"]
    studId = payload["Stud_id"]
    newData = payload["data"]
    appendEntry(request.endpoint, request.method, payload)
    managers[shardName].update(studId, newData)
    response = {
        "message": f"Data entry with Stud_id:{studId} updated",
        "status": "success",
    }
    return response, 200


@app.route("/del", methods=["DELETE"])
def delete():
    payload = request.json
    shardName = payload["shard"]
    studId = payload["Stud_id"]
    appendEntry(request.endpoint, request.method, payload)
    managers[shardName].delete(studId)
    response = {
        "message": f"Data entry with Stud_id:{studId} removed",
        "status": "success",
    }
    return response, 200


@app.route("/getWAL", methods=["GET"])
def getWAL():
    if not os.path.exists("logs"):
        response = {"data": [], "status": "success"}
    else:
        logs = open("logs", "r")
        response = {"data": logs.readlines(), "status": "success"}
        logs.close()
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)