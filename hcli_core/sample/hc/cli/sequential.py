from apscheduler.schedulers.background import BackgroundScheduler
iport queue

# Create an instance of BackgroundScheduler
scheduler = BackgroundScheduler()

# Create a FIFO job queue
job_queue = queue.Queue()

# Define a function to add jobs to the queue
def add_job_to_queue(job_function, *args, **kwargs):
    job_queue.put((job_function, args, kwargs))

# Define a function to process jobs from the queue
def process_job_queue():
    if not job_queue.empty():
        job_function, args, kwargs = job_queue.get()
        job_function(*args, **kwargs)

# Define sample jobs
def job1():
    print("Job 1 executed.")

def job2():
    print("Job 2 executed.")

def job3():
    print("Job 3 executed.")

# Add jobs to the queue
add_job_to_queue(job1)
add_job_to_queue(job2)
add_job_to_queue(job3)

# Start the scheduler
scheduler.add_job(process_job_queue, 'interval', seconds=1)
scheduler.start()

# Keep the script running
try:
    while True:
        pass
except KeyboardInterrupt:
    scheduler.shutdown()
