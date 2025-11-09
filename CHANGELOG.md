# Changelog

## [0.1.0] - 2024-11-09

### Fixed
- Fixed import errors for LeRobot 0.4.0 compatibility
  - Removed unsupported imports: `PolicyFeature`, `FeatureType`, `PipelineFeatureType`
  - Package now works with LeRobot 0.4.0

### Added
- Initial release
- Complete Robot interface implementation
- Support for serial and WiFi connections
- Processor pipelines for action/observation transformations
- 5 example scripts
- Comprehensive documentation

### Notes
- Successfully tested with Roarm M3 robot
- Connection test passes with real hardware
