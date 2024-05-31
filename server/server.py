from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import pika

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

@app.route('/job', methods=['POST'])
def add_job():
    status = 'queued'
    new_job = Job(status=status)
    db.session.add(new_job)
    db.session.commit()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='job_queue')

    channel.basic_publish(exchange='', routing_key='job_queue', body=str(new_job.id))
    print(" [x] Sent 'Job ID: %s'" % new_job.id)
    connection.close()

    return jsonify(job_schema.dump(new_job))

@app.route('/job', methods=['GET'])
def get_jobs():
    all_jobs = Job.query.all()
    result = jobs_schema.dump(all_jobs)
    return jsonify(result)

@app.route('/job/<id>', methods=['GET'])
def get_job(id):
    job = Job.query.get(id)
    return jsonify(job_schema.dump(job))

@app.route('/result', methods=['GET'])
def get_results():
    all_results = Result.query.all()
    result = results_schema.dump(all_results)
    return jsonify(result)

@app.route('/result/<id>', methods=['GET'])
def get_result(id):
    result = Result.query.get(id)
    return jsonify(result_schema.dump(result))

if __name__ == '__main__':
    app.run(debug=True)