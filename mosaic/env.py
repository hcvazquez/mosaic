"""Base environement class."""

import time
import pynisher
import numpy as np

from mosaic.model_score import ScoreModel


class ConfigSpace_env():
    """Base class for environement."""

    terminal_state = []
    bestconfig = {
        "score": 0,
        "model": None
    }

    def __init__(self, eval_func, config_space, logfile = "", mem_in_mb=4048, cpu_time_in_s=5):
        """Constructor."""
        self.history = {}
        self.start_time = time.time()
        self.logfile = logfile
        self.config_space = config_space
        self.nb_parameters = len(self.config_space._hyperparameters)
        self.preprocess = False

        self.score_model = ScoreModel(self.nb_parameters)

        # Constrained evaluation
        self.eval_func = pynisher.enforce_limits(mem_in_mb=mem_in_mb,
                                                 cpu_time_in_s=cpu_time_in_s,
                                                 logger=None)(eval_func)

    def rollout(self, history = []):
        config = self.config_space.sample_partial_configuration(history)
        return config

    def next_moves(self, history = [], info_childs = []):
        try:
            config = self.config_space.sample_partial_configuration(history)
            moves_executed = set([el[0] for el in history])
            full_config = set(config.keys())
            possible_params = list(full_config - moves_executed)
            id_param = self.score_model.most_importance_parameter(
                [self.config_space.get_idx_by_hyperparameter_name(p) for p in possible_params])
            next_param = possible_params[id_param]
            value_param = config[next_param]
            history.append((next_param, value_param))
        except Exception as e:
            print("Exception for {0}".format(history))
            raise(e)
        is_terminal = not self._check_if_same_pipeline([el[0] for el in history], [el for el in config])
        return next_param, value_param, is_terminal


    def _preprocess_moves_util(self, list_moves, index):
        model = list_moves[index][0]
        param_model = {}
        last_index = index
        for i in range(index + 1, len(list_moves)):
            last_index = i
            config, val = list_moves[i]
            if config.startswith(model):
                param_model[config.split("__")[1]] = val
            else:
                break
        return model, param_model, last_index

    def _preprocess_moves(self, list_moves):
        index = 0
        preprocessed_moves = []
        while (index < len(list_moves) - 1):
            model, params, index = self._preprocess_moves_util(list_moves, index)
            preprocessed_moves.append((model, params))
        return preprocessed_moves

    def _evaluate(self, config):
        hash_moves = hash(str(config))
        if hash_moves in self.history:
            return self.history[hash_moves]

        res = self.eval_func(config, self.bestconfig)

        self.score_model.partial_fit(np.nan_to_num(config.get_array()), res)

        if res > self.bestconfig["score"]:
            self.bestconfig = {
                "score": res,
                "model": config
            }
            self.log_result()
            print("Best score", res)

        # Add into history
        self.history[hash_moves] = res
        return res

    def _check_if_same_pipeline(self, pip1, pip2):
        return set(pip1) != set(pip2)

    def has_finite_child(self, history=[]):
        rollout = self.rollout(history)
        return self._check_if_same_pipeline([el for el in rollout], [el[0] for el in history])

    def log_result(self):
        if self.logfile != "":
            with open(self.logfile, "a+") as f:
                f.write("{0},{1}\n".format(time.time() - self.start_time, self.bestconfig["score"]))
