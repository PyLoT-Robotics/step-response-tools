# Source provenance

Developed by PyLoT Robotics from work in `PyLoT-Robotics/pylot_robocup2025`,
commit `55960a6c7bcdaff870a593dedbbb46a7bbeee375`.

The metric definitions and oscillation algorithm are adapted from
`tasks/gaze_arbitration/gaze_arbitration/eval/step_response.py`.
The implementation is rewritten for generic units, fractional tolerances,
explicit observation duration, and single-step validation. Servo commands,
ROS dependencies, motor IDs, and machine motion limits are excluded.

No models, recordings, credentials, or third-party SDKs are bundled.
This standalone project is distributed under Apache-2.0; see LICENSE.
