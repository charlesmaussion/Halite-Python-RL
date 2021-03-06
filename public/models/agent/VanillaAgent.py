"""The Vanilla Agent"""
import numpy as np
import tensorflow as tf
import tensorflow.contrib.slim as slim

from public.models.agent.Agent import Agent


class VanillaAgent(Agent):
    """The Vanilla Agent"""
    def __init__(self, experience=None, lr=1e-2, s_size=9 * 3, a_size=5, h_size=50):  # all these are optional ?
        super(VanillaAgent, self).__init__('vanilla-cin', experience)

        # These lines established the feed-forward part of the network. The agent takes a state and produces an action.
        self.state_in = tf.placeholder(shape=[None, s_size], dtype=tf.float32)

        hidden = slim.fully_connected(self.state_in, h_size, activation_fn=tf.nn.relu)

        self.policy = slim.fully_connected(hidden, a_size, activation_fn=tf.nn.softmax)
        self.predict = tf.argmax(self.policy, 1)

        # The next six lines establish the training proceedure. We feed the reward and predict into the network
        # to compute the loss, and use it to update the network.
        self.reward_holder = tf.placeholder(shape=[None], dtype=tf.float32)
        self.action_holder = tf.placeholder(shape=[None], dtype=tf.int32)

        self.indexes = tf.range(0, tf.shape(self.policy)[0]) * tf.shape(self.policy)[1] + self.action_holder
        self.responsible_outputs = tf.gather(tf.reshape(self.policy, [-1]), self.indexes)
        if experience is not None:
            loss = -tf.reduce_mean(tf.log(self.responsible_outputs) * self.reward_holder)

            self.tvars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=tf.get_variable_scope().name)
            self.gradients = tf.gradients(loss, self.tvars)

            self.gradient_holders = []
            for idx in range(len(self.tvars)):
                placeholder = tf.placeholder(tf.float32, name=str(idx) + '_holder')
                self.gradient_holders.append(placeholder)

            global_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, 'global')
            optimizer = tf.train.AdamOptimizer(learning_rate=lr)

            self.update_global = optimizer.apply_gradients(zip(self.gradient_holders, global_vars))  # self.tvars

    def get_policy(self, sess, state):
        return sess.run(self.policy, feed_dict={self.state_in: [state.reshape(-1)]})

    def choose_action(self, sess, state, frac_progress=1.0, debug=False):  # it only a state, not the game state...
        # Here the state is normalized !
        if np.random.uniform() >= frac_progress:
            a = np.random.choice(range(5))
        else:
            a_dist = sess.run(self.policy, feed_dict={self.state_in: [state.reshape(-1)]})
            a = np.random.choice(a_dist[0], p=a_dist[0])
            a = np.argmax(a_dist == a)
        if debug:
            a = sess.run(self.predict, feed_dict={self.state_in: [state.reshape(-1)]})
        return a

    def update_agent(self, sess):
        # batch_size = min(int(len(self.moves)/2),128) # Batch size
        # indices = np.random.randint(len(self.moves)-1, size=batch_size)
        states, moves, rewards = self.experience.batch(512)

        feed_dict = {self.state_in: states,
                     self.action_holder: moves,
                     self.reward_holder: rewards}
        grads = sess.run(self.gradients, feed_dict=feed_dict)
        feed_dict = dict(zip(self.gradient_holders, grads))
        _ = sess.run(self.update_global, feed_dict=feed_dict)
