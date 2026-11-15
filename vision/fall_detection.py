"""
VIGIL Patient Fall Detection Module
Analyses skeletal pose keypoints, torso angle, aspect ratio, vertical trajectory,
and temporal persistence to identify possible patient falls while distinguishing
normal sitting, bending, and upright postures.
"""
import numpy as np
from typing import Dict, Any, Optional, Tuple
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
        torso_angle_thresh: float = FALL_TORSO_ANGLE_THRESH
    ):
        self.confirmation_frames = confirmation_frames
        self.aspect_ratio_thresh = aspect_ratio_thresh
        self.torso_angle_thresh = torso_angle_thresh

    def analyze_pose(self, bbox: list, keypoints: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Extracts structural posture features from bounding box and keypoints.
        Returns:
            {
                "posture": str ("Upright", "Sitting", "Bending", "Horizontal/Prone", "Unknown"),
                "aspect_ratio": float,
                "torso_angle": float,
                "is_candidate": bool,
                "confidence": float
            }
        """
        x1, y1, x2, y2 = bbox
        width = max(1.0, x2 - x1)
        height = max(1.0, y2 - y1)
        aspect_ratio = width / height

        torso_angle = 0.0
        posture = "Upright"
        is_candidate = False

        if keypoints is not None and len(keypoints) >= 17:
            # Keypoint indices:
            # 5: L_shoulder, 6: R_shoulder
            # 11: L_hip, 12: R_hip
            # 13: L_knee, 14: R_knee
            # 15: L_ankle, 16: R_ankle
            l_sh = keypoints[5]
            r_sh = keypoints[6]
            l_hip = keypoints[11]
            r_hip = keypoints[12]
            l_knee = keypoints[13]
            r_knee = keypoints[14]
            l_ank = keypoints[15]
            r_ank = keypoints[16]

            # Shoulder and hip midpoints
            sh_valid = (l_sh[2] > 0.3 and r_sh[2] > 0.3)
            hip_valid = (l_hip[2] > 0.3 and r_hip[2] > 0.3)

            if sh_valid and hip_valid:
                sh_x = (l_sh[0] + r_sh[0]) / 2.0
                sh_y = (l_sh[1] + r_sh[1]) / 2.0
                hip_x = (l_hip[0] + r_hip[0]) / 2.0
                hip_y = (l_hip[1] + r_hip[1]) / 2.0

                dx = abs(sh_x - hip_x)
                dy = abs(sh_y - hip_y)
                # Angle relative to vertical axis (0 deg = standing straight, 90 deg = flat)
                torso_angle = float(np.degrees(np.arctan2(dx, dy + 1e-6)))

                # Posture classification:
                # Sitting check: Torso is relatively upright (< 40 deg), hips are above knees, knees are above ankles
                knee_valid = (l_knee[2] > 0.3 or r_knee[2] > 0.3)
                ank_valid = (l_ank[2] > 0.3 or r_ank[2] > 0.3)

                if torso_angle > self.torso_angle_thresh and aspect_ratio > 0.95:
                    posture = "Horizontal/Prone"
                    is_candidate = True
                elif torso_angle > 45.0 and aspect_ratio < 0.95 and knee_valid:
                    posture = "Bending"
                    is_candidate = False
                elif torso_angle < 35.0 and aspect_ratio > 0.65 and aspect_ratio < 1.05 and knee_valid and ank_valid:
                    posture = "Sitting"
                    is_candidate = False
                elif torso_angle < 35.0 and aspect_ratio < 0.65:
                    posture = "Upright"
                    is_candidate = False
                else:
                    posture = "Leaning"
            else:
                # Keypoints partially occluded; fallback to bounding box aspect ratio
                if aspect_ratio >= self.aspect_ratio_thresh:
                    posture = "Horizontal/Prone"
                    is_candidate = True
                else:
                    posture = "Upright"
        else:
            # Fallback when keypoints are unavailable
            if aspect_ratio >= self.aspect_ratio_thresh:
                posture = "Horizontal/Prone"
                is_candidate = True
            else:
                posture = "Upright"

        return {
            "posture": posture,
            "aspect_ratio": round(aspect_ratio, 2),
            "torso_angle": round(torso_angle, 1),
            "is_candidate": is_candidate
        }

    def process_track(self, track) -> Tuple[bool, Optional[str]]:
        """
        Processes temporal posture evolution for a given tracked individual.
        Returns:
            (is_fall_detected, description_or_none)
        """
        analysis = self.analyze_pose(track.bbox, track.keypoints)
        track.posture = analysis["posture"]

        if analysis["is_candidate"]:
            track.fall_candidate_frames += 1
            # Check temporal duration threshold
            if track.fall_candidate_frames >= self.confirmation_frames and not track.is_fallen:
                track.is_fallen = True
                desc = (
                    f"Possible patient fall detected for Track #{track.track_id}. "
                    f"Posture transitioned to {analysis['posture']} (Torso angle: {analysis['torso_angle']}°, "
                    f"Aspect ratio: {analysis['aspect_ratio']}) for {track.fall_candidate_frames} consecutive frames."
                )
                return True, desc
        else:
            # Gradual reset if standing back up
            if track.fall_candidate_frames > 0:
                track.fall_candidate_frames = max(0, track.fall_candidate_frames - 2)
            if track.fall_candidate_frames == 0:
                track.is_fallen = False

        return False, None
