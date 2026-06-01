"""Topology and link reliability configuration for the forwarding environment.

This file defines:
- `neighbor_matrix`: directed adjacency matrix of available forwarding links.
- `links`: per-link packet delivery probability (successful transmission rate).
"""

import numpy as np

# Current experiment topology settings.
node_num = 8
parallel_path = 3
max_nb = 2

neighbor_matrix = np.zeros((node_num, node_num))
neighbor_matrix[0][1] = 1
neighbor_matrix[0][2] = 1
neighbor_matrix[0][3] = 1
neighbor_matrix[1][4] = 1
neighbor_matrix[1][5] = 1
neighbor_matrix[2][5] = 1
neighbor_matrix[2][6] = 1
neighbor_matrix[3][6] = 1
neighbor_matrix[4][7] = 1
neighbor_matrix[5][7] = 1
neighbor_matrix[6][7] = 1

links = np.zeros((node_num, node_num))
links[0][1] = 0.77
links[0][2] = 0.76
links[0][3] = 0.77
links[1][4] = 0.75
links[1][5] = 0.76
links[2][5] = 0.76
links[2][6] = 0.77
links[3][6] = 0.78
links[4][7] = 0.77
links[5][7] = 0.75
links[6][7] = 0.76
