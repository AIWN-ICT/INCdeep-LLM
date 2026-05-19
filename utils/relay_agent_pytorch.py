import torch
import torch.nn as nn


class Network_R(nn.Module):
    """Relay-side Q-network.

    The model reshapes the flat relay state, groups neighbor memory blocks, and
    applies shared convolutional feature extraction across neighbors.
    """

    def __init__(self, state_dim, arg_dict, device):
        super(Network_R, self).__init__()
        self.action_dim = arg_dict["action_size"]
        self.state_dim = state_dim
        self.max_nb = arg_dict["max_nb"]
        self.K = arg_dict["K"]
        self.M = arg_dict["M"]
        self.device = device

        self.conv1 = nn.Sequential(
            nn.Conv2d(
                in_channels=arg_dict["max_nb"],
                out_channels=arg_dict["S_conv1_out_channels"],
                kernel_size=arg_dict["S_conv1_kernel_size"],
                stride=1,
                padding="same",
            ),
            nn.ReLU(),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(
                arg_dict["S_conv1_out_channels"],
                arg_dict["S_conv2_out_channels"],
                arg_dict["S_conv2_kernel_size"],
                1,
                "same",
            ),
            nn.ReLU(),
        )
        self.fc1 = nn.Sequential(
            nn.Flatten(),
            nn.Linear(
                arg_dict["S_conv2_out_channels"] * (arg_dict["M"] + 2) * arg_dict["K"],
                arg_dict["fc1_out_features"],
            ),
            nn.ReLU(),
        )
        self.fc2 = nn.Sequential(
            nn.Linear(arg_dict["fc1_out_features"], arg_dict["action_size"]),
        )

    def forward(self, x):
        """Run the relay-side policy network forward pass."""
        x = torch.reshape(x, [-1, 1, (self.M * self.max_nb + 2), self.K])

        # First two rows encode local relay context.
        sliced_x = x[:, :, 0:2, :]
        # Remaining rows encode per-neighbor memory blocks.
        remaining_x = x[:, :, 2:, :]

        split_tensors = []
        for i in range(self.max_nb):
            start_index = i * self.M
            end_index = start_index + self.M
            split_tensor = remaining_x[:, :, start_index:end_index, :]
            split_tensors.append(split_tensor)

        concatenated_tensors = []
        for split_tensor in split_tensors:
            concatenated_tensor = torch.cat((sliced_x, split_tensor), dim=2)
            concatenated_tensors.append(concatenated_tensor)

        final_concatenated_tensor = torch.cat(concatenated_tensors, dim=1)
        x = self.conv1(final_concatenated_tensor)
        x = self.conv2(x)
        x = self.fc1(x)
        x = self.fc2(x)
        return x
