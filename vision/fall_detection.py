"""
VIGIL Patient Fall Detection Module
Analyses skeletal pose keypoints, torso angle, aspect ratio, vertical trajectory,
floor-level proximity, and bed safe zones to distinguish true floor falls from
normal resting/sleeping in a hospital bed, sitting, or bending.
"""
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from config.settings import (
    FALL_CONFIRMATION_FRAMES,
    FALL_ASPECT_RATIO_THRESH,
    FALL_TORSO_ANGLE_THRESH,
    SEVERITY_CRITICAL
)

class FallDetector:
    def __init__(
        self,
        confirmation_frames: int = FALL_CONFIRMATION_FRAMES,
        aspect_ratio_thresh: float = FALL_ASPECT_RATIO_THRESH,
        torso_angle_thresh: float = FALL_TORSO_ANGLE_THRESH,
        floor_level_ratio: float = 0.65  # Normalized Y threshold: floor is bottom 35% of frame
    ):
        self.confirmation_frames = confirmation_frames
        self.aspect_ratio_thresh = aspect_ratio_thresh
        self.torso_angle_thresh = torso_angle_thresh
        self.floor_level_ratio = floor_level_ratio

    def is_in_bed_zone(self, bbox: list, bed_zones: List[Dict[str, Any]], frame_w: int, frame_h: int) -> bool:
        """Checks if a person's center is inside a designated safe bed / stretcher zone."""
        if not bed_zones:
            return False
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0

        for zone in bed_zones:
            zx1 = zone["x1"] * frame_w if zone["x1"] <= 1.0 else zone["x1"]
            zy1 = zone["y1"] * frame_h if zone["y1"] <= 1.0 else zone["y1"]
            zx2 = zone["x2"] * frame_w if zone["x2"] <= 1.0 else zone["x2"]
            zy2 = zone["y2"] * frame_h if zone["y2"] <= 1.0 else zone["y2"]

            if min(zx1, zx2) <= cx <= max(zx1, zx2) and min(zy1, zy2) <= cy <= max(zy1, zy2):
                return True
        return False

    def analyze_pose(
        self,
        bbox: list,
        keypoints: Optional[np.ndarray],
        frame_h: int = 480,
        frame_w: int = 640,
        bed_zones: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extracts structural posture features, verifies ground/floor contact,
        and checks bed zone occupancy to prevent false positives from sleeping patients.
        """
        x1, y1, x2, y2 = bbox
        width = max(1.0, x2 - x1)
        height = max(1.0, y2 - y1)
        aspect_ratio = width / height

        # Normalized floor contact elevation: y2 is the lowest point of the person
        normalized_y2 = y2 / max(1.0, float(frame_h))
        is_at_floor_level = (normalized_y2 >= self.floor_level_ratio)

        # Check if inside designated Bed Zone
        in_bed = self.is_in_bed_zone(bbox, bed_zones or [], frame_w, frame_h)

        torso_angle = 0.0
        posture = "Upright"
        is_candidate = False

        if keypoints is not None and len(keypoints) >= 17:
            # Keypoint indices: 5: L_sh, 6: R_sh, 11: L_hip, 12: R_hip, 13: L_knee, 14: R_knee, 15: L_ank, 16: R_ank
            l_sh = keypoints[5]
            r_sh = keypoints[6]
            l_hip = keypoints[11]
            r_hip = keypoints[12]
            l_knee = keypoints[13]
            r_knee = keypoints[14]
            l_ank = keypoints[15]
            r_ank = keypoints[16]

            sh_valid = (l_sh[2] > 0.3 and r_sh[2] > 0.3)
            hip_valid = (l_hip[2] > 0.3 and r_hip[2] > 0.3)

            if sh_valid and hip_valid:
                sh_x = (l_sh[0] + r_sh[0]) / 2.0
                sh_y = (l_sh[1] + r_sh[1]) / 2.0
                hip_x = (l_hip[0] + r_hip[0]) / 2.0
                hip_y = (l_hip[1] + r_hip[1]) / 2.0

                dx = abs(sh_x - hip_x)
                dy = abs(sh_y - hip_y)
                torso_angle = float(np.degrees(np.arctan2(dx, dy + 1e-6)))

                knee_valid = (l_knee[2] > 0.3 or r_knee[2] > 0.3)
                ank_valid = (l_ank[2] > 0.3 or r_ank[2] > 0.3)

                # Check if prone
                if torso_angle > self.torso_angle_thresh and aspect_ratio > 0.95:
                    if in_bed or not is_at_floor_level:
                        # Patient is horizontal on an elevated bed / stretcher
                        posture = "Lying in Bed (Resting)"
                        is_candidate = False
                    else:
                        # Patient is horizontal on the floor
                        posture = "Horizontal / Floor Fall"
                        is_candidate = True
                elif torso_angle > 45.0 and aspect_ratio < 0.95 and knee_valid:
                    posture = "Bending"
                    is_candidate = False
                elif torso_angle < 35.0 and 0.65 < aspect_ratio < 1.05 and knee_valid and ank_valid:
                    posture = "Sitting"
                    is_candidate = False
                elif torso_angle < 35.0 and aspect_ratio < 0.65:
                    posture = "Upright"
                    is_candidate = False
                else:
                    posture = "Leaning"
            else:
                # Keypoints partially occluded; fallback with floor check
                if aspect_ratio >= self.aspect_ratio_thresh:
                    if in_bed or not is_at_floor_level:
                        posture = "Lying in Bed (Resting)"
                        is_candidate = False
                    else:
                        posture = "Horizontal / Floor Fall"
                        is_candidate = True
                else:
                    posture = "Upright"
        else:
            if aspect_ratio >= self.aspect_ratio_thresh:
                if in_bed or not is_at_floor_level:
                    posture = "Lying in Bed (Resting)"
                    is_candidate = False
                else:
                    posture = "Horizontal / Floor Fall"
                    is_candidate = True
            else:
                posture = "Upright"

        return {
            "posture": posture,
            "aspect_ratio": round(aspect_ratio, 2),
            "torso_angle": round(torso_angle, 1),
            "is_at_floor_level": is_at_floor_level,
            "in_bed": in_bed,
            "is_candidate": is_candidate
        }

    def process_track(
        self,
        track,
        frame_h: int = 480,
        frame_w: int = 640,
        bed_zones: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Processes temporal posture evolution for a given tracked individual.
        Only triggers a fall alert if the patient is on the floor (outside bed zones).
        """
        analysis = self.analyze_pose(track.bbox, track.keypoints, frame_h, frame_w, bed_zones)
        track.posture = analysis["posture"]

        if analysis["is_candidate"]:
            track.fall_candidate_frames += 1
            if track.fall_candidate_frames >= self.confirmation_frames and not track.is_fallen:
                track.is_fallen = True
                desc = (
                    f"Possible patient floor fall detected for Track #{track.track_id}. "
                    f"Posture collapsed to {analysis['posture']} (Floor level contact confirmed: Y={track.bbox[3]:.0f}px, "
                    f"Torso angle: {analysis['torso_angle']}°, Aspect ratio: {analysis['aspect_ratio']}) "
                    f"for {track.fall_candidate_frames} consecutive frames."
                )
                return True, desc
        else:
            if track.fall_candidate_frames > 0:
                track.fall_candidate_frames = max(0, track.fall_candidate_frames - 2)
            if track.fall_candidate_frames == 0:
                track.is_fallen = False

        return False, None
