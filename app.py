from flask import Flask,request,jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


app.config["MONGO_URI"] = "mongodb://localhost:27017/Users"

# mongodb+srv://sumit:<password>@cluster0.uuqyj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority
mongo = PyMongo(app)

secret = "OneAssure"


def tokenReq(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') #http://127.0.0.1:5000/users?token=alshfjfjdklsfj89549834ur

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403

        try: 
            data = jwt.decode(token, secret)
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated


#user registration
@app.route("/register", methods=['POST'])
# mongo.db.record.insert(dict(Name=data['name'],Age=data['age']))
def register():
    message = ""
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        check = mongo.db.record.find(dict(email=data['email']))
        if check.count() >= 1:
            message = "User already exists :("
            code = 401
            status = "fail"
        else:
            res = mongo.db.record.insert_one(dict(name=data['name'],phone=data['phone'],email=data['email'],password=data['password'])) 
            status = "successful"
            message = "user registered successfully!"
            code = 201
    except Exception as ex:
        message = f"{ex}"
        status = "fail"
        code = 500
    return jsonify({'status': status, "message": message}), 200


@app.route('/login', methods=['POST'])
def login():
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        user =  mongo.db.record.find_one({"email": data['email']})
        if user:
            user['_id'] = str(user['_id'])
            if user and user['password'] == data['password']:
                time = datetime.utcnow() + timedelta(hours=24)
                token = jwt.encode({
                        "user": {
                            "email": f"{user['email']}",
                            "id": f"{user['_id']}",
                        },
                        "exp": time
                    },secret)

                del user['password']

                message = f"user authenticated"
                code = 200
                status = "successful"
                res_data['token']=token.decode('UTF-8')
                res_data['user'] = user

                
            else:
                message = "wrong password"
                code = 401
                status = "fail"
        else:
            message = "invalid login details"
            code = 401
            status = "fail"

    except Exception as ex:
        message = f"{ex}"
        code = 500
        status = "fail"
    return jsonify({'status': status, "data": res_data, "message":message}), code


@app.route('/users', methods=['GET'])
@tokenReq
def getusers():
    data = []
    code = 500
    message = ""
    status = "fail"

    try:
        page=int(request.args.get('page'))
        print(page)
        
        count=mongo.db.record.find({}).count()
        print(count)
        
        for oneresult in mongo.db.record.find({}).skip(5*(page-1)).limit(5):
            oneresult['_id'] = str(oneresult['_id'])
            data.append(oneresult)


        if data:
            message = "users data fetched successfully"
            status = "successful"
            code = 201
        else:
            message = "No users found :("
            status = "fail"
            code = 404

    except Exception as ee:
        message =  str(ee)
        status = "Error"

    return jsonify({"status": status, "message":message,'data': data, 'total_page' : int(count/5 +1), 'total_users':count}), code

if __name__ == "__main__":
    app.run(debug=True)