
from cmath import log
from codecs import encode
from xmlrpc.client import boolean
from flask import Flask,request, make_response, jsonify
#from flask_restful import Api
#from flask_api import status
import hashlib
import psycopg2
import random
import re
import datetime


app = Flask(__name__)
#api = Api(app)

def log_activity():
    conn = connect_db()
    cur=conn.cursor()
    cur.execute("INSERT INTO log(ip_address, activity_timestamp, activity_url, activity_method) VALUES(%s, %s, %s, %s)",
    (request.remote_addr, datetime.datetime.now(), request.base_url, request.method))
    conn.commit()
    cur.close()
    conn.close()

def generate_salt():
    alphabet="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@!'^+%&/()=?*-_>£#${[]}"
    salt=[]
    for i in range(8):
        salt.append(random.choice(alphabet))
    return "".join(salt)


def connect_db():
    conn = psycopg2.connect(
        host="172.17.0.1",
        database="flask_db",
        user="mert",
        password="123456")
    return conn

@app.route("/getlogs", methods=["GET"])
def get_logs():
    conn=connect_db()
    cur=conn.cursor()
    cur.execute("SELECT * FROM log;")
    logs=cur.fetchall()
    #print(logs)
    log_list=[]
    for log in logs:
        log_json={"ip_address":log[0],
                    "activity_timestamp":log[1],
                    "activity_url":log[2],
                    "activity_method":log[3],
                    }
        log_list.append(log_json)
    response = make_response(jsonify(log_list),200)
    return response

@app.route("/login", methods=["POST"])
def login():
    username=request.json["username"]
    password=request.json['password']
    conn=connect_db()
    cur=conn.cursor()
    log_activity()
    try:
        cur.execute("SELECT password, salt FROM USERS WHERE username=username;", (username))
    except:
        response=make_response(jsonify({"message" : "login failed: user not found"}), 200)
        return response
    pw=cur.fetchall()
    password+=pw[0][1]
    if hashlib.sha256(encode(password)).hexdigest() == pw[0][0]:
        
        try:
            cur.execute("INSERT INTO online_users(username, ip_address, logindatetime) VALUES (%s, %s, %s);",(username, request.remote_addr, datetime.datetime.now()))
            conn.commit()
            cur.close()
            conn.close()
        except:
            response=make_response(jsonify({"message" : "login failed:you are logged in to a different account, logout first"}), 200)
            return response
        response=make_response(jsonify({"message" : "login successful"}), 200)
        return response
    else:
        response=make_response(jsonify({"message" : "login failed: wrong password"}), 401)
        return response

@app.route("/logout", methods=["GET"])
def logout():
    log_activity()
    conn=connect_db()
    cur=conn.cursor()
    #print(request.remote_addr)
    cur.execute("DELETE FROM online_users WHERE ip_address = ip_address;",(request.remote_addr))
    conn.commit()
    cur.close()
    conn.close()
    response=make_response(jsonify({"message" : "logout successful"}), 200)
    return response

@app.route("/user/list", methods=["GET"])
def list():
    log_activity()
    conn=connect_db()
    cur=conn.cursor()
    cur.execute("SELECT * from users;")
    users = cur.fetchall()
    cur.close()
    conn.close()
    user_list=[]
    i=0
    for user in users:
        user_json={"username":user[0],
                    "firstname":user[1],
                    "middlename":user[2],
                    "lastname":user[3],
                    "birthdate":user[4],
                    "email":user[5],
                    "password":user[6],
                    "salt":user[7]
                    }
        user_list.append(user_json)
        i+=1
    response = make_response(jsonify(user_list),200)
    return response

@app.route("/user/create", methods=["POST"])
def register():
    #print("qweqwe"    )
    log_activity()
    try:
        username=request.json['username']
        firstname=request.json['firstname']
        middlename=request.json['middlename']
        lastname=request.json['lastname']
        birthdate=request.json['birthdate']
        email=request.json['email']
        password=request.json['password']
    except:
        response=make_response(jsonify({"message":"error, wrong or missing credentials"}),406)
        return response
    if re.fullmatch("(?:[A-Z]+)(?:[a-z]+)(?:[0-9]+)",password) == None or len(password)<8:
        response=make_response(jsonify({"message":"password should be 8 characters minimum and contain at"
        " least an uppercase, a lowercase character and a number"}),406)
        return response
    elif re.fullmatch(".+@[a-z]+[.][a-z]{2,}",email) == None:
        response=make_response(jsonify({"message":"wrong email format"}),406)
        return response
    conn=connect_db()
    cur=conn.cursor()
    salt=generate_salt()
    password+=salt
    try:
        cur.execute("INSERT INTO users(username, firstname, middlename, lastname, birthdate, email, password, salt)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",(username, firstname, middlename, lastname, birthdate, email, hashlib.sha256(encode(password)).hexdigest(), salt))
    except:
        response=make_response(jsonify({"message":"username already in use"}),406)
        return response
    conn.commit()
    cur.close()
    conn.close()
    response=make_response(jsonify({"message":"registration successful"}),200)
    return response

@app.route("/user/delete/<username>", methods=["DELETE"])
def delete(username):
    log_activity()
    conn=connect_db()
    cur=conn.cursor()
    try:
        cur.execute("DELETE FROM USERS WHERE username=username;",(username))
    except:
        response=make_response(jsonify({"message" : "user not found"}), 200)
        return response
    conn.commit()
    cur.close()
    conn.close()
    response=make_response(jsonify({"message" : "user successfully deleted"}), 200)
    return response

@app.route("/user/update/<username>", methods=["POST"])
def update(username):
    log_activity()
    conn=connect_db()
    cur=conn.cursor()
    try:
        firstname=request.json['firstname']
        middlename=request.json['middlename']
        lastname=request.json['lastname']
        birthdate=request.json['birthdate']
        email=request.json['email']
        password=request.json['password']
    except:
        response=make_response(jsonify({"message":"update failed: wrong or missing credentials"}),406)
        return response
    if re.fullmatch("(?:[A-Z]+)(?:[a-z]+)(?:[0-9]+)",password) == None or len(password)<8:
        response=make_response(jsonify({"message":"update failed: password should be 8 characters "
        "minimum and contain at least an uppercase, a lowercase character and a number"}),406)
        return response
    elif re.fullmatch(".+@[a-z]+[.][a-z]{2,}",email) == None:
        response=make_response(jsonify({"message":"update failed: wrong email format"}),406)
        return response
    cur.execute("UPDATE USERS SET firstname=firstname, middlename=middlename, lastname=lastname, birthdate=birthdate, email=email, password=password WHERE username=username;",
    (firstname, middlename, lastname, birthdate, email, password))
    conn.commit()
    cur.close()
    conn.close()
    response=make_response(jsonify({"message" : "user successfully updated"}), 200)
    return response

@app.route("/onlineusers", methods=["GET"])
def list_online_users():
    log_activity()
    conn=connect_db()
    cur=conn.cursor()
    cur.execute("SELECT * from online_users;")
    users = cur.fetchall()
    cur.close()
    conn.close()
    user_list=[]
    i=0
    for user in users:
        user_json={"username":user[0],
                    "ip":user[1],
                    "logindatetime":user[2],
                    }
        user_list.append(user_json)
        i+=1
    response = make_response(jsonify(user_list),200)
    return response

@app.errorhandler(404)
def notfound(error):
    log_activity()
    response=make_response(jsonify({"message":"page not found"}),404)
    return response

if __name__=='__main__':
    app.run(host='0.0.0.0')
