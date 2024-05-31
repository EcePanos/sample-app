from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import json
import redis
import pika

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://yourusername:yourpassword@localhost/yourdatabase'
db = SQLAlchemy(app)
ma = Marshmallow(app)
r = redis.Redis(host='redis', port=6379, db=0)

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
    r.delete('jobs')  # Invalidate the cache
    connection.close()

    return jsonify(job_schema.dump(new_job))

@app.route('/job', methods=['GET'])
def get_jobs():
    jobs = r.get('jobs')
    if jobs is None:
        all_jobs = Job.query.all()
        jobs = jobs_schema.dumps(all_jobs)
        r.set('jobs', jobs)
    return jsonify(json.loads(jobs))

@app.route('/job/<id>', methods=['GET'])
def get_job(id):
    job = r.get(f'job:{id}')
    if job is None:
        job = Job.query.get(id)
        job = job_schema.dumps(job)
        r.set(f'job:{id}', job)
    return jsonify(json.loads(job))

@app.route('/result', methods=['GET'])
def get_results():
    results = r.get('results')
    if results is None:
        all_results = Result.query.all()
        results = results_schema.dumps(all_results)
        r.set('results', results)
    return jsonify(json.loads(results))

@app.route('/result/<id>', methods=['GET'])
def get_result(id):
    result = r.get(f'result:{id}')
    if result is None:
        result = Result.query.get(id)
        result = result_schema.dumps(result)
        r.set(f'result:{id}', result)
    return jsonify(json.loads(result))

if __name__ == '__main__':
    app.run(debug=True)