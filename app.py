from pyexpat.errors import messages
from urllib import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_jwt_extended import create_access_token,jwt_required,JWTManager
from flask_mail import Mail, Message
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret' #change this IRL
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIl_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
#app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
#app.config['MAIL_PORT'] = 2525
#app.config['MAIL_USERNAME'] = 'd9c52f48c0acc0'
#app.config['MAIL_PASSWORD'] = '********4e34'
#app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USE_SSL'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)



@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('database created.')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('database dropped.')

@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star = 'Sol',
                     mass = 3.258e23,
                     radius = 1516,
                     distance = 35.98e6)

    venus = Planet(planet_name='Venus',
                     planet_type='Class K',
                     home_star='Sol',
                     mass=4.868e24,
                     radius=3760,
                     distance=67.98e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.977e24,
                   radius=3959,
                   distance=92.98e6)
    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name="Ruiyu",
                     last_name='Huang',
                     email='test@test.com',
                     password='p@ssW0rd')
    db.session.add(test_user)
    db.session.commit()
    print('Database seeded!')
@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='Hello from the Planetary API,booya'),200


@app.route('/not_found')
def not_found():
    return jsonify(message='That resources was Not Found'), 404

@app.route('/parameters')
def parameters():
    name= request.args.get('name')
    age = int(request.args.get('age'))

    if age <18:
        return jsonify(message='sorry'+name+',you are too young.'),401
    else:
        return jsonify(message='Welcome'+name+',you are old enough.'),200

@app.route('/url_variable/<string:name>/<int:age>')
def url_variable(name: str,age: int):
    if age <18:
        return jsonify(message='sorry'+name+',you are too young.'),401
    else:
        return jsonify(message='Welcome'+name+',you are old enough.'),200

@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)
@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email is already registered.'),409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='Thank you for registering!'), 201

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded.",access_token=access_token)
    else:
        return jsonify(message="Invalid email or password."),401
@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email:str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Your planetary API password is ' + 'user.password',
                      sender='admin@planetary-api.com',
                      recipients= [email])
        mail.send(msg)
        return jsonify(message='Password send to '+ email)
    else:
        return jsonify(message='That email doesnt exist'),401


@app.route('/planet_details/<int:planet_id>',methods = ['GET'])
def planet_details(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message='That planet doesnt exist'),401


@app.route('/add_planet',methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.args.get('planet_name')
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message='That planet already exists.'),409
    else:
        planet_type = request.args.get('planet_type')
        home_star = request.args.get('home_star')
        mass = float(request.args.get('mass'))
        radius = float(request.args.get('radius'))
        distance = float(request.args.get('distance'))

        new_planet  = Planet(planet_name=planet_name,
                             planet_type=planet_type,
                             home_star=home_star,
                             mass=mass,
                             radius=radius,
                             distance=distance)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message='Planet added successfully.'),201

@app.route('/update_planet',methods=['PUT'])
@jwt_required()
def update_planet():
    planet_id = int(request.args.get('planet_id'))
    planet = Planet.query.filter_by(planet_id = planet_id).first()
    if planet:
        planet.planet_name = request.args.get('planet_name')
        planet.planet_type = request.args.get('planet_type')
        planet.home_star = request.args.get('home_star')
        planet.mass = request.args.get('mass')
        planet.radius = request.args.get('radius')
        planet.distance = request.args.get('distance')
        db.session.commit()
        return jsonify(message='Planet updated successfully.'),201
    else:
        return jsonify(message='That planet doesnt exist'),401

@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_planet(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message='Planet removed successfully.'),201
    else:
        return jsonify(message='That planet doesnt exist'),401


#database models
class User(db.Model):
    '''control the name of the table'''
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50),unique=True)
    password = Column(String(50))

class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String(50))
    planet_type = Column(String(50))
    home_star = Column(String(50))
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')

class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')

user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run()
