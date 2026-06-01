from __future__ import annotations

import numpy as np


class NODE:
    def __init__(self, K, M, id):
        self.id = id
        self.receivememory = np.zeros((M, K))
        self.codelen = 0
        self.receivelen = 0
        self.datamemory = []
        self.sendmemory = []
        self.codememory = np.zeros((M, K))
        self.receive_flag = False
        self.list_action = np.zeros(K)
        self.list_state = []
        self.list_n_state = []
        self.list_rewards = np.zeros(K)
        self.list_len = 0
        self.packet = []
        self.received_source_send_ids = set()

    def getpacket(self):
        packet = self.packet[0]
        if len(self.packet) > 1:
            temp = []
            for i in range(1, len(self.packet)):
                temp.append(self.packet[i])
            self.packet = temp
        else:
            self.packet = []
        return packet