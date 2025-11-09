# Changelog

## [0.1.0] - 2025-11-09

### Added
- Initial release of LeRobot Roarm integration
- Complete Robot interface implementation for LeRobot 0.4.1
- Support for serial (USB) and WiFi connections
- Roarm teleoperator implementation for leader-follower control
- Support for SO-101 leader arm with automatic percentage-to-degree scaling
- Proper logging system (replaced all print statements)
- Processor pipelines for action/observation transformations
- 5 example scripts demonstrating various use cases
- VSCode debug configuration for teleoperation
- Comprehensive documentation (README, QUICKSTART, PROJECT_STRUCTURE)

### Fixed
- Fixed package structure (flattened nested directories)
- Fixed joint angle limits (using actual hardware limits from SDK)
- Fixed SO-101 percentage mapping (-100% to +100% → full joint ranges)
- Commented out SDK debug output (roarm_sdk common.py line 320)
- Auto-detection of value type (radians vs percentages) in send_action()

### Tested
- ✅ Roarm-to-Roarm teleoperation (serial & WiFi)
- ✅ SO-101-to-Roarm teleoperation with proper scaling
- ✅ Proper logging output (no SDK spam)
- ✅ pip install from GitHub works correctly
- ✅ Joint limits enforced correctly per joint

### Technical Details
- Compatible with LeRobot 0.4.1 (main branch, commit a4aa316)
- Uses roarm-sdk 0.1.0
- Package installable via: `pip install git+https://github.com/koenvanwijk/roarm.git`
- Joint naming follows LeRobot standard convention
- Asymmetric joint limits properly configured (e.g., elbow_flex: -70° to 190°)
