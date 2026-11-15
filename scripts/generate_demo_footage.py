"""
VIGIL Demo Footage Generator
Generates realistic benchmark video footage simulating a hospital corridor with:
1. Patient walking and experiencing a sudden collapse / fall
2. Attendant placing a bag and leaving it unattended
3. Multiple healthcare staff congregating (crowd alert & correlated emergency)
4. Movement into restricted zone
"""
import os
import cv2
import numpy as np
from pathlib import Path

def draw_stick_figure(canvas, center_x, center_y, scale=1.0, posture="upright", color=(235, 235, 235)):
    """Draws a human figure with realistic body proportions."""
    cx, cy = int(center_x), int(center_y)
    head_radius = int(14 * scale)
    torso_len = int(55 * scale)
    arm_len = int(35 * scale)
    leg_len = int(50 * scale)

    if posture == "upright":
        # Head
        cv2.circle(canvas, (cx, cy - torso_len - head_radius), head_radius, color, -1, cv2.LINE_AA)
        # Torso
        cv2.line(canvas, (cx, cy - torso_len), (cx, cy), color, int(4 * scale), cv2.LINE_AA)
        # Arms
        cv2.line(canvas, (cx - arm_len, cy - int(torso_len * 0.7)), (cx + arm_len, cy - int(torso_len * 0.7)), color, int(3 * scale), cv2.LINE_AA)
        # Legs
        cv2.line(canvas, (cx, cy), (cx - int(leg_len * 0.35), cy + leg_len), color, int(4 * scale), cv2.LINE_AA)
        cv2.line(canvas, (cx, cy), (cx + int(leg_len * 0.35), cy + leg_len), color, int(4 * scale), cv2.LINE_AA)

    elif posture == "prone":  # Fallen on the floor
        # Head on ground
        cv2.circle(canvas, (cx - torso_len - head_radius, cy), head_radius, color, -1, cv2.LINE_AA)
        # Horizontal Torso
        cv2.line(canvas, (cx - torso_len, cy), (cx, cy), color, int(4 * scale), cv2.LINE_AA)
        # Arms spread
        cv2.line(canvas, (cx - int(torso_len * 0.7), cy - int(arm_len * 0.5)), (cx - int(torso_len * 0.7), cy + int(arm_len * 0.5)), color, int(3 * scale), cv2.LINE_AA)
        # Legs extended
        cv2.line(canvas, (cx, cy), (cx + leg_len, cy - int(leg_len * 0.1)), color, int(4 * scale), cv2.LINE_AA)
        cv2.line(canvas, (cx, cy), (cx + leg_len, cy + int(leg_len * 0.1)), color, int(4 * scale), cv2.LINE_AA)

    elif posture == "sitting":
        # Head
        cv2.circle(canvas, (cx, cy - int(torso_len * 0.8) - head_radius), head_radius, color, -1, cv2.LINE_AA)
        # Torso
        cv2.line(canvas, (cx, cy - int(torso_len * 0.8)), (cx, cy), color, int(4 * scale), cv2.LINE_AA)
        # Thighs horizontal
        cv2.line(canvas, (cx, cy), (cx + int(leg_len * 0.5), cy), color, int(4 * scale), cv2.LINE_AA)
        # Lower legs vertical
        cv2.line(canvas, (cx + int(leg_len * 0.5), cy), (cx + int(leg_len * 0.5), cy + int(leg_len * 0.5)), color, int(4 * scale), cv2.LINE_AA)

def generate_hospital_corridor_video(output_path: str, duration_sec: int = 15, fps: int = 20):
    w, h = 640, 480
    total_frames = duration_sec * fps
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        # Hospital corridor background
        frame = np.full((h, w, 3), (240, 243, 245), dtype=np.uint8)  # Light clinical wall

        # Floor (Perspective polygon)
        floor_pts = np.array([[0, h], [w, h], [int(w * 0.75), int(h * 0.42)], [int(w * 0.25), int(h * 0.42)]], np.int32)
        cv2.fillPoly(frame, [floor_pts], (210, 218, 224))

        # Corridor lines & baseboards
        cv2.line(frame, (0, h), (int(w * 0.25), int(h * 0.42)), (180, 190, 200), 2)
        cv2.line(frame, (w, h), (int(w * 0.75), int(h * 0.42)), (180, 190, 200), 2)
        cv2.line(frame, (int(w * 0.25), int(h * 0.42)), (int(w * 0.75), int(h * 0.42)), (170, 180, 190), 2)

        # Hospital Corridor Doors & Signs
        cv2.rectangle(frame, (int(w * 0.08), int(h * 0.3)), (int(w * 0.22), int(h * 0.65)), (190, 205, 215), 2)
        cv2.putText(frame, "ROOM 204", (int(w * 0.10), int(h * 0.28)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 140, 160), 1)

        # Medication Cart Zone indicator on floor
        cart_zone = np.array([[int(w * 0.05), int(h * 0.75)], [int(w * 0.35), int(h * 0.75)], [int(w * 0.32), int(h * 0.60)], [int(w * 0.12), int(h * 0.60)]], np.int32)
        cv2.polylines(frame, [cart_zone], True, (60, 60, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, "MED CART ZONE", (int(w * 0.08), int(h * 0.72)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (60, 60, 200), 1)

        # Scenario Simulation Timeline:
        # 0s - 3s: Patient (Person 1) walks down corridor (upright)
        # 3s - 4s: Patient stumbles and transitions to fall
        # 4s - 15s: Patient remains prone on floor (FALL ALERT)
        # 5s - 9s: Attendant (Person 2) enters, walks into restricted zone, drops a bag
        # 10s - 15s: Multiple staff members (Persons 3, 4, 5) rush in (CROWD + CORRELATED ALERT)

        # 1. Patient
        if t < 3.0:
            p1_x = int(w * 0.45 + (t / 3.0) * (w * 0.05))
            p1_y = int(h * 0.55 + (t / 3.0) * (h * 0.15))
            draw_stick_figure(frame, p1_x, p1_y, scale=1.1, posture="upright", color=(50, 80, 140))
        elif t < 3.8:
            # Transitioning
            p1_x = int(w * 0.50 + (t - 3.0) * 20)
            p1_y = int(h * 0.70 + (t - 3.0) * 35)
            draw_stick_figure(frame, p1_x, p1_y, scale=1.1, posture="prone", color=(50, 80, 140))
        else:
            # Fallen prone on the floor
            draw_stick_figure(frame, int(w * 0.52), int(h * 0.78), scale=1.1, posture="prone", color=(50, 80, 140))

        # 2. Attendant entering restricted zone & bag
        if 4.5 <= t <= 11.0:
            att_x = int(w * 0.15 + (t - 4.5) * 15)
            att_y = int(h * 0.68)
            draw_stick_figure(frame, att_x, att_y, scale=1.0, posture="upright", color=(80, 120, 70))

        # Bag left on floor from t >= 6.5s
        if t >= 6.5:
            # Draw backpack
            cv2.rectangle(frame, (int(w * 0.24), int(h * 0.68)), (int(w * 0.28), int(h * 0.73)), (40, 50, 80), -1)
            cv2.putText(frame, "Bag", (int(w * 0.24), int(h * 0.67)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (40, 50, 80), 1)

        # 3. Crowd Gathering (Staff rushing to assist patient)
        if t >= 9.5:
            draw_stick_figure(frame, int(w * 0.38), int(h * 0.72), scale=1.0, posture="upright", color=(100, 60, 60))
            draw_stick_figure(frame, int(w * 0.62), int(h * 0.74), scale=1.0, posture="upright", color=(70, 70, 110))
        if t >= 11.0:
            draw_stick_figure(frame, int(w * 0.44), int(h * 0.68), scale=0.9, posture="upright", color=(60, 100, 100))
            draw_stick_figure(frame, int(w * 0.68), int(h * 0.70), scale=0.9, posture="upright", color=(90, 80, 60))

        out.write(frame)

    out.release()
    print(f"Generated demo video: {output_path} ({total_frames} frames)")

if __name__ == "__main__":
    out_dir = Path("data/videos")
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_hospital_corridor_video(str(out_dir / "demo_hospital_corridor.mp4"), duration_sec=12, fps=15)
