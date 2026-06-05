"""Track selected tip points from an actuator video and export displacement data."""

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Experiment constants and display options

clicked_points = []
N_POINTS = 3  # Number of tip points to track and save

def mouse_callback(event, x, y, flags, param):
    global clicked_points

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) >= N_POINTS:
            print(f"Already selected {N_POINTS} points. Press ENTER or SPACE to continue.")
            return
        clicked_points.append((x, y))
        print(f"Clicked point {len(clicked_points)}/{N_POINTS}: x={x}, y={y}")

VIDEO_NAME = "pinecone2.mp4"
DISPLAY_SCALE = 0.4
PIXELS_PER_MM = 9.8611  # ImageJ calibration value (px/mm)

# Use this when the preview appears rotated or upside down.
# Options: None, "rotate_90_clockwise", "rotate_90_counterclockwise", "rotate_180",
#          "flip_horizontal", "flip_vertical"
FRAME_ORIENTATION = "rotate_90_clockwise"

def correct_frame_orientation(frame):
    if FRAME_ORIENTATION is None:
        return frame
    if FRAME_ORIENTATION == "rotate_90_clockwise":
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if FRAME_ORIENTATION == "rotate_90_counterclockwise":
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if FRAME_ORIENTATION == "rotate_180":
        return cv2.rotate(frame, cv2.ROTATE_180)
    if FRAME_ORIENTATION == "flip_horizontal":
        return cv2.flip(frame, 1)
    if FRAME_ORIENTATION == "flip_vertical":
        return cv2.flip(frame, 0)
    raise ValueError(f"Unknown FRAME_ORIENTATION: {FRAME_ORIENTATION}")

# Preview and annotation settings
SAVE_VIDEO_ORIGINAL_SIZE = True
POINT_RADIUS = 14
POINT_THICKNESS = -1
TRACK_LINE_THICKNESS = 5
ROI_LINE_THICKNESS = 4
TEXT_SCALE = 1.4
TEXT_THICKNESS = 4
# Reserved label parameters; point labels are not drawn in the current output.
LABEL_TEXT_SCALE = 1.2 * 1.7
LABEL_TEXT_THICKNESS = 4

# Point colors are defined in OpenCV BGR order.
POINT_COLORS_BGR = [
    (64, 64, 241),    # #F14040
    (223, 111, 26),   # #1A6FDF
    (107, 173, 55),   # #37AD6B
]

# Input and output locations

BASE_DIR = Path(__file__).resolve().parent
video_path = BASE_DIR / VIDEO_NAME

# Images saved for checking the selected tracking points
selected_points_image_path = BASE_DIR / "selected_tip_points.png"
selected_points_image_small_path = BASE_DIR / "selected_tip_points_display_size.png"

print("Video path:", video_path)
print("Video exists:", video_path.exists())
print("Calibration:", PIXELS_PER_MM, "pixels/mm")

if not video_path.exists():
    raise FileNotFoundError(f"Video not found: {video_path}")

# Open the video and read the first frame

cap = cv2.VideoCapture(str(video_path))

try:
    cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)
except Exception:
    pass


if not cap.isOpened():
    raise RuntimeError("Video file could not be opened.")

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print("FPS:", fps)
print("Total frames:", total_frames)

ret, first_frame = cap.read()

if not ret:
    raise RuntimeError("Could not read first frame.")

first_frame = correct_frame_orientation(first_frame)

# Select the region used for manual point picking

small_first = cv2.resize(first_frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)

roi_small = cv2.selectROI(
    "Select scale tip ROI, then press ENTER or SPACE",
    small_first,
    fromCenter=False,
    showCrosshair=True
)

cv2.destroyAllWindows()

x_s, y_s, w_s, h_s = map(int, roi_small)

if w_s == 0 or h_s == 0:
    raise RuntimeError("ROI was not selected.")

x = int(x_s / DISPLAY_SCALE)
y = int(y_s / DISPLAY_SCALE)
w = int(w_s / DISPLAY_SCALE)
h = int(h_s / DISPLAY_SCALE)

print("Selected ROI original coordinates:")
print("x:", x, "y:", y, "w:", w, "h:", h)

# Pick initial tip positions in the first frame

old_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

clicked_points.clear()

manual_view = first_frame.copy()

cv2.rectangle(
    manual_view,
    (x, y),
    (x + w, y + h),
    (255, 0, 0),
    2
)

manual_small = cv2.resize(manual_view, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)

window_name = f"Click exactly {N_POINTS} tip points, then press ENTER"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, mouse_callback)

while True:
    temp = manual_small.copy()

    for i, (px, py) in enumerate(clicked_points):
        color = POINT_COLORS_BGR[i % len(POINT_COLORS_BGR)]
        cv2.circle(temp, (px, py), 7, color, -1)

    cv2.imshow(window_name, temp)

    key = cv2.waitKey(1) & 0xFF

    if key == 13 or key == 32:  # ENTER or SPACE
        if len(clicked_points) == N_POINTS:
            break
        print(f"Please select exactly {N_POINTS} points. Current: {len(clicked_points)}")

    if key == 27:
        raise RuntimeError("Manual point selection cancelled.")

cv2.destroyAllWindows()

if len(clicked_points) != N_POINTS:
    raise RuntimeError(f"Exactly {N_POINTS} points must be selected. Selected: {len(clicked_points)}")

manual_points = []

for x_click_s, y_click_s in clicked_points:
    x_click = int(x_click_s / DISPLAY_SCALE)
    y_click = int(y_click_s / DISPLAY_SCALE)
    manual_points.append([[x_click, y_click]])

p0 = np.array(manual_points, dtype=np.float32)

print("All manual tracking points:")
print(p0.reshape(-1, 2))

print(f"All {N_POINTS} clicked points will be saved for displacement analysis.")

# Save a reference image of the selected tracking points

check = first_frame.copy()

# Mark the selected region
cv2.rectangle(
    check,
    (x, y),
    (x + w, y + h),
    (255, 0, 0),
    2
)

# Mark the initial tracking points on the full-resolution frame
for i, point in enumerate(p0.reshape(-1, 2)):
    px, py = point.astype(int)

    color = POINT_COLORS_BGR[i % len(POINT_COLORS_BGR)]
    radius = POINT_RADIUS + 2 if i == 0 else POINT_RADIUS

    cv2.circle(check, (px, py), radius, color, POINT_THICKNESS)

cv2.putText(
    check,
    "Selected tracking points",
    (30, 55),
    cv2.FONT_HERSHEY_SIMPLEX,
    TEXT_SCALE,
    (0, 0, 255),
    TEXT_THICKNESS
)

# Keep a full-resolution copy for records
cv2.imwrite(str(selected_points_image_path), check)
print("Saved selected points image:", selected_points_image_path)

# Also keep a smaller copy for quick inspection
check_small = cv2.resize(check, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
cv2.imwrite(str(selected_points_image_small_path), check_small)
print("Saved selected points display image:", selected_points_image_small_path)

cv2.imshow("Selected tracking points - press any key", check_small)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Optical-flow initialization

initial_point = p0.copy()
old_points = p0.copy()

lk_params = dict(
    winSize=(21, 21),
    maxLevel=3,
    criteria=(
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
        30,
        0.01
    )
)

# Canvas used to accumulate the point trajectories over time.
draw_mask = np.zeros_like(first_frame)

# Opacity of the trajectory overlay on the saved tracking video.
TRAIL_ALPHA = 0.60

data = []
frame_idx = 0

# Prepare the annotated tracking video

output_video_path = BASE_DIR / "sparse_tracking_result.mp4"

if SAVE_VIDEO_ORIGINAL_SIZE:
    output_size = (first_frame.shape[1], first_frame.shape[0])
else:
    output_size = (
        int(first_frame.shape[1] * DISPLAY_SCALE),
        int(first_frame.shape[0] * DISPLAY_SCALE)
    )

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

out = cv2.VideoWriter(
    str(output_video_path),
    fourcc,
    fps if fps > 0 else 30,
    output_size
)

print("Output video path:", output_video_path)
print("Output video size:", output_size)

# Track each selected point frame by frame

while True:
    ret, frame = cap.read()

    if not ret:
        print("End of video or failed to read frame.")
        break

    frame = correct_frame_orientation(frame)

    frame_idx += 1

    if frame_idx % 30 == 0:
        print(f"Processing frame {frame_idx}/{total_frames}")

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    new_points, status, error = cv2.calcOpticalFlowPyrLK(
        old_gray,
        frame_gray,
        old_points,
        None,
        **lk_params
    )

    if new_points is None or status is None:
        print("Optical flow failed.")
        break

    status_flat = status.reshape(-1)

    good_new = new_points[status_flat == 1]
    good_old = old_points[status_flat == 1]
    good_initial = initial_point[status_flat == 1]

    if len(good_new) < 1:
        print("All tracking points lost.")
        break

    time_s = frame_idx / fps if fps > 0 else frame_idx

    row = {
        "frame": frame_idx,
        "time_s": time_s
    }

    # Store coordinates and displacement values for each selected point.
    for i in range(N_POINTS):
        point_id = i + 1
        tracked_ok = int(status_flat[i]) == 1

        if tracked_ok:
            new_point = new_points[i, 0]
            init_point = initial_point[i, 0]

            dx_px = float(new_point[0] - init_point[0])
            dy_px = float(new_point[1] - init_point[1])
            disp_px = float(np.sqrt(dx_px**2 + dy_px**2))

            row[f"p{point_id}_status"] = 1
            row[f"p{point_id}_x_px"] = float(new_point[0])
            row[f"p{point_id}_y_px"] = float(new_point[1])
            row[f"p{point_id}_dx_px"] = dx_px
            row[f"p{point_id}_dy_px"] = dy_px
            row[f"p{point_id}_disp_px"] = disp_px
            row[f"p{point_id}_dx_mm"] = dx_px / PIXELS_PER_MM
            row[f"p{point_id}_dy_mm"] = dy_px / PIXELS_PER_MM
            row[f"p{point_id}_disp_mm"] = disp_px / PIXELS_PER_MM
        else:
            # Missing tracks are recorded as NaN to avoid artificial displacement values.
            row[f"p{point_id}_status"] = 0
            row[f"p{point_id}_x_px"] = np.nan
            row[f"p{point_id}_y_px"] = np.nan
            row[f"p{point_id}_dx_px"] = np.nan
            row[f"p{point_id}_dy_px"] = np.nan
            row[f"p{point_id}_disp_px"] = np.nan
            row[f"p{point_id}_dx_mm"] = np.nan
            row[f"p{point_id}_dy_mm"] = np.nan
            row[f"p{point_id}_disp_mm"] = np.nan

    data.append(row)

    if frame_idx % 30 == 0:
        disp_msg = ", ".join(
            [f"p{i+1}: {row[f'p{i+1}_disp_mm']:.4f} mm" if row[f"p{i+1}_status"] == 1 else f"p{i+1}: lost"
             for i in range(N_POINTS)]
        )
        print("Displacement - " + disp_msg)

    # Draw the current tracking result

    vis = frame.copy()

    cv2.rectangle(
        vis,
        (x, y),
        (x + w, y + h),
        (255, 0, 0),
        2
    )

    # Extend the trajectory trace for each successfully tracked point.
    for idx in range(N_POINTS):
        if int(status_flat[idx]) != 1:
            continue

        new = new_points[idx, 0]
        old = old_points[idx, 0]

        a, b = new.ravel().astype(int)
        c, d = old.ravel().astype(int)

        point_color = POINT_COLORS_BGR[idx % len(POINT_COLORS_BGR)]

        cv2.line(
            draw_mask,
            (a, b),
            (c, d),
            point_color,
            TRACK_LINE_THICKNESS
        )

    # Blend only trajectory pixels so the original frame remains unchanged elsewhere.
    trail_pixels = np.any(draw_mask > 0, axis=2)

    if np.any(trail_pixels):
        vis[trail_pixels] = cv2.addWeighted(
            vis[trail_pixels],
            1.0 - TRAIL_ALPHA,
            draw_mask[trail_pixels],
            TRAIL_ALPHA,
            0
        )

    # Draw the current point locations above the traces.
    for idx in range(N_POINTS):
        if int(status_flat[idx]) != 1:
            continue

        new = new_points[idx, 0]
        a, b = new.ravel().astype(int)

        point_color = POINT_COLORS_BGR[idx % len(POINT_COLORS_BGR)]

        cv2.circle(
            vis,
            (a, b),
            POINT_RADIUS,
            point_color,
            POINT_THICKNESS
        )

    cv2.putText(
        vis,
        f"Frame: {frame_idx}/{total_frames}",
        (30, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        TEXT_SCALE,
        (0, 0, 255),
        TEXT_THICKNESS
    )

    disp_text = " | ".join(
        [f"P{i+1}: {row[f'p{i+1}_disp_mm']:.3f} mm" if row[f"p{i+1}_status"] == 1 else f"P{i+1}: lost"
         for i in range(N_POINTS)]
    )
    cv2.putText(
        vis,
        disp_text,
        (30, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        TEXT_SCALE * 0.85,
        (0, 0, 255),
        TEXT_THICKNESS
    )

    # Use a scaled preview window while keeping the saved video at the chosen resolution.
    vis_small = cv2.resize(vis, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
    cv2.imshow("Sparse Optical Flow Tracking - ESC to stop", vis_small)

    # Write the annotated frame.
    if SAVE_VIDEO_ORIGINAL_SIZE:
        out.write(vis)
    else:
        out.write(vis_small)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        print("Stopped by ESC.")
        break

    old_gray = frame_gray.copy()
    old_points = new_points.reshape(-1, 1, 2)

cap.release()
out.release()
cv2.destroyAllWindows()

print("Saved tracking video:", output_video_path)

# Export the displacement table

if len(data) == 0:
    raise RuntimeError("No tracking data was collected.")

df = pd.DataFrame(data)

csv_path = BASE_DIR / "three_points_displacement_sparse.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print("Saved CSV:", csv_path)

# Quick plot for checking the displacement history

plt.figure()
for i in range(N_POINTS):
    point_id = i + 1
    plt.plot(df["time_s"], df[f"p{point_id}_disp_mm"], label=f"Point {point_id}")
plt.xlabel("Time (s)")
plt.ylabel("Displacement (mm)")
plt.title("Pine cone scale tip displacement - 3 points")
plt.legend()
plt.grid(True)
plt.show()
