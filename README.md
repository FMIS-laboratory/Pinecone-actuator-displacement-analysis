# Pinecone Actuator Displacement Analysis

This repository contains custom scripts used for humidity-dependent voltage control and video-based displacement analysis of a pinecone-inspired actuator.

The scripts were used to characterize the humidity-responsive actuation behavior of the device by combining automated humidity-dependent voltage switching with optical-flow-based tracking of selected tip points from recorded actuation videos.

## Repository contents

```text
pinecone-actuator-displacement-analysis/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
│
├── scripts/
│   ├── video_displacement_tracking.py
│   └── humidity_voltage_control.ino
│
└── example_data/
    └── three_points_displacement_sparse.csv
```

## Scripts

### `scripts/video_displacement_tracking.py`

This Python script tracks manually selected tip points from an actuation video using sparse optical flow based on the pyramidal Lucas-Kanade method.

The script performs the following steps:

1. Loads an actuation video.
2. Allows the user to select a region of interest.
3. Allows the user to manually select three tip points in the first frame.
4. Tracks the selected points throughout the video.
5. Calculates the displacement of each point relative to its initial position.
6. Converts pixel displacement to millimeters using an ImageJ-derived calibration factor.
7. Exports the tracking results as a CSV file.

The current script uses the following calibration factor:

```python
PIXELS_PER_MM = 9.8611
```

This value should be modified according to the calibration of each video.

### `scripts/humidity_voltage_control.ino`

This Arduino script reads relative humidity using an SHT4x humidity sensor and controls relay outputs according to predefined humidity ranges.

The voltage condition is selected as follows:

| Relative humidity range | Applied voltage |
| ----------------------- | --------------- |
| RH < 50%                | 0 V             |
| 50% ≤ RH < 70%          | 1 V             |
| RH ≥ 70%                | 3.5 V           |

Humidity values and relay states are printed through serial communication at 1 s intervals.

## Python requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages:

```text
opencv-python
numpy
pandas
matplotlib
```

## Usage

### 1. Video-based displacement tracking

Place the actuation video in the same directory as the Python script, or modify the video path in the script.

In the script, set the input video name:

```python
VIDEO_NAME = "pinecone2.mp4"
```

Set the pixel-to-mm calibration factor:

```python
PIXELS_PER_MM = 9.8611
```

Run the script:

```bash
python scripts/video_displacement_tracking.py
```

During execution, select the region of interest and then click the tip points to be tracked in the first frame.

The script generates the following output files:

| Output file                            | Description                                             |
| -------------------------------------- | ------------------------------------------------------- |
| `selected_tip_points.png`              | Image showing the initially selected tracking points    |
| `selected_tip_points_display_size.png` | Display-size version of the selected point image        |
| `sparse_tracking_result.mp4`           | Video showing the tracked point trajectories            |
| `three_points_displacement_sparse.csv` | Time-dependent displacement data of the selected points |

### 2. Humidity-dependent voltage control

Upload the Arduino sketch to the microcontroller after connecting the SHT4x humidity sensor and relay circuit.

The script reads the relative humidity and switches the relay outputs according to the predefined humidity ranges. The humidity and relay states can be monitored through the serial monitor.

## Example data

The `example_data/three_points_displacement_sparse.csv` file provides an example of the displacement data exported from the video tracking script.

The CSV file includes:

* frame number
* time
* tracking status of each point
* x and y coordinates in pixels
* x and y displacement components in pixels
* resultant displacement in pixels
* x and y displacement components in millimeters
* resultant displacement in millimeters

## Notes

Raw video files are not included in this repository due to file size. Representative videos may be provided as supplementary materials in the related manuscript.

The calibration factor, number of tracking points, and input video name should be adjusted depending on the experimental video.

## Related manuscript

This repository supports the experimental methods and displacement analysis described in the related manuscript.

Manuscript title: TBD

## License

This project is licensed under the MIT License.
