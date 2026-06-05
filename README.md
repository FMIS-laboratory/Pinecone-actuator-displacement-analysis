# Pinecone Actuator Displacement Analysis

This repository contains custom scripts used for humidity-dependent voltage control and video-based displacement analysis of a pinecone-inspired actuator.

## Contents

- `scripts/video_displacement_tracking.py`  
  Tracks manually selected tip points from actuation videos using sparse optical flow and calculates displacement in millimeters.

- `scripts/humidity_voltage_control.ino`  
  Reads relative humidity using an SHT4x humidity sensor and controls relay outputs according to predefined humidity ranges.

- `example_data/three_points_displacement_sparse.csv`  
  Example displacement data exported from the video tracking script.

## Python requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
