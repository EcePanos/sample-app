from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import pika
import time
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://yourusername:yourpassword@localhost/yourdatabase'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10))

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    number = db.Column(db.Integer)

class JobSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Job

class ResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Result

job_schema = JobSchema()
jobs_schema = JobSchema(many=True)
result_schema = ResultSchema()
results_schema = ResultSchema(many=True)

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    job_id = int(body)
    job = Job.query.get(job_id)
    if job:
        job.status = 'ongoing'
        db.session.commit()

        time.sleep(5)

        result = Result(job_id=job_id, number=random.randint(1, 100))
        db.session.add(result)

        job.status = 'complete'
        db.session.commit()
        print(" [x] Job %r complete" % job_id)
    else:
        print(" [x] No job found with id %r" % job_id)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()

channel.queue_declare(queue='job_queue')

channel.basic_consume(queue='job_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()