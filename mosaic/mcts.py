"""Monte carlo tree seach class."""

import random

import logging
import math
import networkx as nx

from mosaic.policy import UCT
from mosaic.node import Node


class MCTS():
    """Monte carlo tree search implementation."""

    def __init__(self, env, logfile=''):
        """Initialization."""
        # environement
        self.env = env

        # Init tree
        self.tree = Node()

        # Set up logger
        if logfile != '':
            self.logger = logging.getLogger('mcts')
            hdlr = logging.FileHandler(logfile, mode='w')
            formatter = logging.Formatter('%(asctime)s %(message)s')
            hdlr.setFormatter(formatter)
            self.logger.addHandler(hdlr)
            self.logger.setLevel(logging.DEBUG)

        # Policy
        self.policy = UCT()

    def MCT_SEARCH(self):
        """MCTS method."""
        front = self.TREEPOLICY()
        reward = self.random_policy(front)
        self.BACKUP(front, reward)
        #return self.policy.BESTCHILD(, 0)

    def TREEPOLICY(self):
        """Search for the best child node."""
        SCALAR = 1 / math.sqrt(2.0)

        node = 0 # Root of the tree
        while not self.tree.is_terminal(node):
            childs = [self.tree.get_info_node(n) for n in self.tree.get_childs(node)]
            if len(childs) == 0:
                return self.EXPAND(node)
            else:
                if not self.tree.fully_expanded(node, self.env.space):
                    return self.EXPAND(node)
                else:
                    node = self.policy.BESTCHILD(self.tree.get_info_node(node), childs, SCALAR)
        return node

    def EXPAND(self, node):
        """Expand child node."""
        name, value, terminal = self.env.space.next_params(self.tree.get_path_to_node(node),
                                                            self.tree.get_childs(node, info = ["name", "value"]))
        return self.tree.add_node(name=name, value=value, terminal=terminal, parent_node = node)

    def random_policy(self, node_id):
        """Random policy."""
        playout_node = self.env.rollout(self.tree.get_path_to_node(node_id))
        return self.env._evaluate(playout_node)

    def BACKUP(self, node, reward):
        """Back propagate reward."""
        self.tree.backprop_from_node(node, reward)

    def run(self, n=1, generate_image_path = ""):
        """Play 1 simulation."""
        for i in range(n):
            self.MCT_SEARCH()
            if generate_image_path != "":
                self.tree.draw_tree("{0}/{1}.png".format(generate_image_path, i))
