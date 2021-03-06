"""This main.py file runs the training."""
import threading
import os
import sys
import tensorflow as tf

from public.models.agent.VanillaAgent import VanillaAgent
from train.experience import ExperienceVanilla
from train.worker import Worker

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


port = int(sys.argv[1]) if len(sys.argv) > 1 else 2000

tf.reset_default_graph()  # Clear the Tensorflow graph.

with tf.device("/cpu:0"):
    lr = 1e-3
    s_size = 9 * 3
    a_size = 5
    h_size = 50

    with tf.variable_scope('global'):
        master_experience = ExperienceVanilla()
        master_agent = VanillaAgent(master_experience, lr, s_size, a_size, h_size)

    num_workers = 5
    n_simultations = 500

    workers = []
    if num_workers > 1:
        for i in range(num_workers):
            with tf.variable_scope('worker_' + str(i)):
                workers.append(Worker(port, i, VanillaAgent(ExperienceVanilla(), lr, s_size, a_size, h_size)))
    else:
        workers.append(Worker(port, 0, master_agent))
    # We need only to save the global
    global_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='global')
    saver = tf.train.Saver(global_variables)
    init = tf.global_variables_initializer()

# Launch the tensorflow graph
with tf.Session() as sess:
    sess.run(init)
    try:
        saver.restore(sess, os.path.abspath(
            os.path.dirname(__file__)) + '/../public/models/variables/' + master_agent.name + '/' + master_agent.name)
    except FileNotFoundError:
        print("Model not found - initiating new one")

    coord = tf.train.Coordinator()
    worker_threads = []
    print("I'm the main thread running on CPU")

    if num_workers == 1:
        workers[0].work(sess, saver, n_simultations)
    else:
        for worker in workers:
            worker_work = lambda worker=worker: worker.work(sess, saver, n_simultations)
            t = threading.Thread(target=(worker_work))  # Process instead of threading.Thread multiprocessing.Process
            t.start()
            worker_threads.append(t)
        coord.join(worker_threads)
