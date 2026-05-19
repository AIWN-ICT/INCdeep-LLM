<<<<<<< HEAD
from __future__ import annotations

import csv
import os
import re

import numpy as np


def sanitize_filename(name: str, fallback: str = "output") -> str:
    """Return a GitHub-friendly and cross-platform safe filename.

    Rules:
    - keep only ASCII letters, digits, dot, underscore, hyphen
    - collapse repeated separators
    - strip leading/trailing separators and dots
    - avoid Windows reserved names
    """
    if not isinstance(name, str):
        name = str(name)

    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    safe = re.sub(r"_+", "_", safe)
    safe = re.sub(r"-+", "-", safe)
    safe = safe.strip("._-")

    if not safe:
        safe = fallback

    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    if safe.upper() in reserved:
        safe = f"{fallback}_{safe.lower()}"

    return safe


def std_dev(data):
    """Return the population standard deviation of the input sequence."""
    return np.std(data)


def ensure_folder_exists(folder_path):
    """Create the target directory if it does not already exist."""
    os.makedirs(folder_path, exist_ok=True)


def write_counts_to_csv(source_send_count_list, file_path, file_name):
    """Write per-episode source transmission counts to a single-column CSV file."""
    ensure_folder_exists(file_path)
    safe_name = sanitize_filename(file_name, fallback="counts")
    csv_file_path = os.path.join(file_path, safe_name)
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows([[count] for count in source_send_count_list])


def calculate_decode_probability(source_send_count_list):
    """Compute decode success probability for packet thresholds from 1 to 60.

    For each threshold i, this returns the fraction of episodes whose source
    transmission count is less than or equal to i.
    """
    decode_probability = []
    for i in range(1, 61):
        decode_success_count = sum(1 for j in source_send_count_list if j <= i)
        decode_probability.append(decode_success_count / len(source_send_count_list))
    return decode_probability


def write_results_to_csv(name, decode_probabilities, avg_overhead, std_dev_count, avg_s_f, data_folder):
    """Export decode probability curve and summary statistics to a CSV file.

    The first data row includes aggregate metrics (`avg_overhead`, `std_dev`,
    and `avg_s_f`) to keep compatibility with existing downstream readers.
    """
    safe_base_name = sanitize_filename(name, fallback="results")
    filename = os.path.join(data_folder, f"{safe_base_name}.csv")
    ensure_folder_exists(data_folder)
    overhead_row_index = 1
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["sent packet", "Probability", "avg_overhead", "std_dev", "avg_s_f"])
        for index, prob in enumerate(decode_probabilities, start=1):
            if index == overhead_row_index:
                writer.writerow([index, prob, avg_overhead, std_dev_count, avg_s_f])
            else:
                writer.writerow([index, prob, ""])
=======
from __future__ import annotations

import csv
import os
import re

import numpy as np


def sanitize_filename(name: str, fallback: str = "output") -> str:
    """Return a GitHub-friendly and cross-platform safe filename.

    Rules:
    - keep only ASCII letters, digits, dot, underscore, hyphen
    - collapse repeated separators
    - strip leading/trailing separators and dots
    - avoid Windows reserved names
    """
    if not isinstance(name, str):
        name = str(name)

    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    safe = re.sub(r"_+", "_", safe)
    safe = re.sub(r"-+", "-", safe)
    safe = safe.strip("._-")

    if not safe:
        safe = fallback

    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    if safe.upper() in reserved:
        safe = f"{fallback}_{safe.lower()}"

    return safe


def std_dev(data):
    """Return the population standard deviation of the input sequence."""
    return np.std(data)


def ensure_folder_exists(folder_path):
    """Create the target directory if it does not already exist."""
    os.makedirs(folder_path, exist_ok=True)


def write_counts_to_csv(source_send_count_list, file_path, file_name):
    """Write per-episode source transmission counts to a single-column CSV file."""
    ensure_folder_exists(file_path)
    safe_name = sanitize_filename(file_name, fallback="counts")
    csv_file_path = os.path.join(file_path, safe_name)
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows([[count] for count in source_send_count_list])


def calculate_decode_probability(source_send_count_list):
    """Compute decode success probability for packet thresholds from 1 to 60.

    For each threshold i, this returns the fraction of episodes whose source
    transmission count is less than or equal to i.
    """
    decode_probability = []
    for i in range(1, 61):
        decode_success_count = sum(1 for j in source_send_count_list if j <= i)
        decode_probability.append(decode_success_count / len(source_send_count_list))
    return decode_probability


def write_results_to_csv(name, decode_probabilities, avg_overhead, std_dev_count, avg_s_f, data_folder):
    """Export decode probability curve and summary statistics to a CSV file.

    The first data row includes aggregate metrics (`avg_overhead`, `std_dev`,
    and `avg_s_f`) to keep compatibility with existing downstream readers.
    """
    safe_base_name = sanitize_filename(name, fallback="results")
    filename = os.path.join(data_folder, f"{safe_base_name}.csv")
    ensure_folder_exists(data_folder)
    overhead_row_index = 1
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["sent packet", "Probability", "avg_overhead", "std_dev", "avg_s_f"])
        for index, prob in enumerate(decode_probabilities, start=1):
            if index == overhead_row_index:
                writer.writerow([index, prob, avg_overhead, std_dev_count, avg_s_f])
            else:
                writer.writerow([index, prob, ""])
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
