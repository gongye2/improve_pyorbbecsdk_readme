from __future__ import annotations
from pyorbbecsdk.pyorbbecsdk import AccelFrame
from pyorbbecsdk.pyorbbecsdk import AccelStreamProfile
from pyorbbecsdk.pyorbbecsdk import AlignFilter
from pyorbbecsdk.pyorbbecsdk import CameraParamList
from pyorbbecsdk.pyorbbecsdk import ColorFrame
from pyorbbecsdk.pyorbbecsdk import ConfidenceFrame
from pyorbbecsdk.pyorbbecsdk import Config
from pyorbbecsdk.pyorbbecsdk import Context
from pyorbbecsdk.pyorbbecsdk import DecimationFilter
from pyorbbecsdk.pyorbbecsdk import DepthFrame
from pyorbbecsdk.pyorbbecsdk import Device
from pyorbbecsdk.pyorbbecsdk import DeviceInfo
from pyorbbecsdk.pyorbbecsdk import DeviceList
from pyorbbecsdk.pyorbbecsdk import DevicePresetList
from pyorbbecsdk.pyorbbecsdk import DisparityTransform
from pyorbbecsdk.pyorbbecsdk import Filter
from pyorbbecsdk.pyorbbecsdk import FormatConvertFilter
from pyorbbecsdk.pyorbbecsdk import Frame
from pyorbbecsdk.pyorbbecsdk import FrameSet
from pyorbbecsdk.pyorbbecsdk import GyroFrame
from pyorbbecsdk.pyorbbecsdk import GyroStreamProfile
from pyorbbecsdk.pyorbbecsdk import HDRMergeFilter
from pyorbbecsdk.pyorbbecsdk import HoleFillingFilter
from pyorbbecsdk.pyorbbecsdk import IRFrame
from pyorbbecsdk.pyorbbecsdk import LiDARPointsFrame
from pyorbbecsdk.pyorbbecsdk import LiDARStreamProfile
from pyorbbecsdk.pyorbbecsdk import NoiseRemovalFilter
from pyorbbecsdk.pyorbbecsdk import OBAccelFullScaleRange
from pyorbbecsdk.pyorbbecsdk import OBAccelIntrinsic
from pyorbbecsdk.pyorbbecsdk import OBAccelValue as OBGyroValue
from pyorbbecsdk.pyorbbecsdk import OBAccelValue as OBFloat3D
from pyorbbecsdk.pyorbbecsdk import OBAccelValue
from pyorbbecsdk.pyorbbecsdk import OBAlignMode
from pyorbbecsdk.pyorbbecsdk import OBBaselineCalibrationParam
from pyorbbecsdk.pyorbbecsdk import OBBoolPropertyRange
from pyorbbecsdk.pyorbbecsdk import OBCalibrationParam
from pyorbbecsdk.pyorbbecsdk import OBCameraDistortion
from pyorbbecsdk.pyorbbecsdk import OBCameraDistortionModel
from pyorbbecsdk.pyorbbecsdk import OBCameraIntrinsic
from pyorbbecsdk.pyorbbecsdk import OBCameraParam
from pyorbbecsdk.pyorbbecsdk import OBCmdVersion
from pyorbbecsdk.pyorbbecsdk import OBColorPoint
from pyorbbecsdk.pyorbbecsdk import OBCommunicationType
from pyorbbecsdk.pyorbbecsdk import OBCompressionMode
from pyorbbecsdk.pyorbbecsdk import OBCompressionParams
from pyorbbecsdk.pyorbbecsdk import OBConvertFormat
from pyorbbecsdk.pyorbbecsdk import OBCoordinateSystemType
from pyorbbecsdk.pyorbbecsdk import OBDCPowerState
from pyorbbecsdk.pyorbbecsdk import OBDDONoiseRemovalType
from pyorbbecsdk.pyorbbecsdk import OBDataTranState
from pyorbbecsdk.pyorbbecsdk import OBDepthCroppingMode
from pyorbbecsdk.pyorbbecsdk import OBDepthPrecisionLevel
from pyorbbecsdk.pyorbbecsdk import OBDepthWorkMode
from pyorbbecsdk.pyorbbecsdk import OBDepthWorkModeList
from pyorbbecsdk.pyorbbecsdk import OBDepthWorkModeTag
from pyorbbecsdk.pyorbbecsdk import OBDeviceAccessMode
from pyorbbecsdk.pyorbbecsdk import OBDeviceDevelopmentMode
from pyorbbecsdk.pyorbbecsdk import OBDeviceIpAddrConfig
from pyorbbecsdk.pyorbbecsdk import OBDeviceSyncConfig
from pyorbbecsdk.pyorbbecsdk import OBDeviceTemperature
from pyorbbecsdk.pyorbbecsdk import OBDeviceTimestampResetConfig
from pyorbbecsdk.pyorbbecsdk import OBDeviceType
from pyorbbecsdk.pyorbbecsdk import OBEdgeNoiseRemovalFilterParams
from pyorbbecsdk.pyorbbecsdk import OBEdgeNoiseRemovalType
from pyorbbecsdk.pyorbbecsdk import OBError
from pyorbbecsdk.pyorbbecsdk import OBException
from pyorbbecsdk.pyorbbecsdk import OBExtrinsic
from pyorbbecsdk.pyorbbecsdk import OBFileTranState
from pyorbbecsdk.pyorbbecsdk import OBFilterConfigSchemaItem
from pyorbbecsdk.pyorbbecsdk import OBFilterConfigValueType
from pyorbbecsdk.pyorbbecsdk import OBFilterList
from pyorbbecsdk.pyorbbecsdk import OBFloatPropertyRange
from pyorbbecsdk.pyorbbecsdk import OBFormat
from pyorbbecsdk.pyorbbecsdk import OBFrameAggregateOutputMode
from pyorbbecsdk.pyorbbecsdk import OBFrameMetadataType
from pyorbbecsdk.pyorbbecsdk import OBFrameType
from pyorbbecsdk.pyorbbecsdk import OBGyroFullScaleRange
from pyorbbecsdk.pyorbbecsdk import OBGyroIntrinsic
from pyorbbecsdk.pyorbbecsdk import OBGyroSampleRate
from pyorbbecsdk.pyorbbecsdk import OBGyroSampleRate as OBAccelSampleRate
from pyorbbecsdk.pyorbbecsdk import OBHardwareDecimationConfig
from pyorbbecsdk.pyorbbecsdk import OBHdrConfig
from pyorbbecsdk.pyorbbecsdk import OBHoleFillingMode
from pyorbbecsdk.pyorbbecsdk import OBIntPropertyRange
from pyorbbecsdk.pyorbbecsdk import OBLiDARPoint
from pyorbbecsdk.pyorbbecsdk import OBLiDARScanPoint
from pyorbbecsdk.pyorbbecsdk import OBLiDARScanRate
from pyorbbecsdk.pyorbbecsdk import OBLiDARSpherePoint
from pyorbbecsdk.pyorbbecsdk import OBLogLevel
from pyorbbecsdk.pyorbbecsdk import OBMediaState
from pyorbbecsdk.pyorbbecsdk import OBMediaType
from pyorbbecsdk.pyorbbecsdk import OBMultiDeviceSyncConfig
from pyorbbecsdk.pyorbbecsdk import OBMultiDeviceSyncMode
from pyorbbecsdk.pyorbbecsdk import OBNoiseRemovalFilterParams
from pyorbbecsdk.pyorbbecsdk import OBPermissionType
from pyorbbecsdk.pyorbbecsdk import OBPixelType
from pyorbbecsdk.pyorbbecsdk import OBPlaybackStatus
from pyorbbecsdk.pyorbbecsdk import OBPoint2f
from pyorbbecsdk.pyorbbecsdk import OBPoint3f
from pyorbbecsdk.pyorbbecsdk import OBPowerLineFreqMode
from pyorbbecsdk.pyorbbecsdk import OBPresetResolutionConfig
from pyorbbecsdk.pyorbbecsdk import OBPropertyID
from pyorbbecsdk.pyorbbecsdk import OBPropertyItem
from pyorbbecsdk.pyorbbecsdk import OBPropertyType
from pyorbbecsdk.pyorbbecsdk import OBProtocolVersion
from pyorbbecsdk.pyorbbecsdk import OBRect
from pyorbbecsdk.pyorbbecsdk import OBRegionOfInterest
from pyorbbecsdk.pyorbbecsdk import OBRotateDegreeType
from pyorbbecsdk.pyorbbecsdk import OBSensorType
from pyorbbecsdk.pyorbbecsdk import OBSequenceIdItem
from pyorbbecsdk.pyorbbecsdk import OBSpatialAdvancedFilterParams
from pyorbbecsdk.pyorbbecsdk import OBStatus
from pyorbbecsdk.pyorbbecsdk import OBStreamType
from pyorbbecsdk.pyorbbecsdk import OBSyncMode
from pyorbbecsdk.pyorbbecsdk import OBTofExposureThresholdControl
from pyorbbecsdk.pyorbbecsdk import OBTofFilterRange
from pyorbbecsdk.pyorbbecsdk import OBUSBPowerState
from pyorbbecsdk.pyorbbecsdk import OBUint16PropertyRange
from pyorbbecsdk.pyorbbecsdk import OBUint8PropertyRange
from pyorbbecsdk.pyorbbecsdk import OBUpgradeState
from pyorbbecsdk.pyorbbecsdk import Pipeline
from pyorbbecsdk.pyorbbecsdk import PlaybackDevice
from pyorbbecsdk.pyorbbecsdk import PointCloudFilter
from pyorbbecsdk.pyorbbecsdk import PointsFrame
from pyorbbecsdk.pyorbbecsdk import PresetResolutionConfigList
from pyorbbecsdk.pyorbbecsdk import RecordDevice
from pyorbbecsdk.pyorbbecsdk import Sensor
from pyorbbecsdk.pyorbbecsdk import SensorList
from pyorbbecsdk.pyorbbecsdk import SequenceIdFilter
from pyorbbecsdk.pyorbbecsdk import SpatialAdvancedFilter
from pyorbbecsdk.pyorbbecsdk import StreamProfile
from pyorbbecsdk.pyorbbecsdk import StreamProfileList
from pyorbbecsdk.pyorbbecsdk import TemporalFilter
from pyorbbecsdk.pyorbbecsdk import ThresholdFilter
from pyorbbecsdk.pyorbbecsdk import VideoFrame
from pyorbbecsdk.pyorbbecsdk import VideoStreamProfile
from pyorbbecsdk.pyorbbecsdk import get_version
from pyorbbecsdk.pyorbbecsdk import save_lidar_point_cloud_to_ply
from pyorbbecsdk.pyorbbecsdk import save_point_cloud_to_ply
from pyorbbecsdk.pyorbbecsdk import transformation2dto2d
from pyorbbecsdk.pyorbbecsdk import transformation2dto3d
from pyorbbecsdk.pyorbbecsdk import transformation3dto2d
from pyorbbecsdk.pyorbbecsdk import transformation3dto3d
from . import pyorbbecsdk
__all__: list[str] = ['AccelFrame', 'AccelStreamProfile', 'AlignFilter', 'COUNT', 'CameraParamList', 'ColorFrame', 'ConfidenceFrame', 'Config', 'Context', 'DecimationFilter', 'DepthFrame', 'Device', 'DeviceInfo', 'DeviceList', 'DevicePresetList', 'DisparityTransform', 'Filter', 'FormatConvertFilter', 'Frame', 'FrameSet', 'GyroFrame', 'GyroStreamProfile', 'HDRMergeFilter', 'HoleFillingFilter', 'IRFrame', 'LiDARPointsFrame', 'LiDARStreamProfile', 'NoiseRemovalFilter', 'OBAccelFullScaleRange', 'OBAccelIntrinsic', 'OBAccelSampleRate', 'OBAccelValue', 'OBAlignMode', 'OBBaselineCalibrationParam', 'OBBoolPropertyRange', 'OBCalibrationParam', 'OBCameraDistortion', 'OBCameraDistortionModel', 'OBCameraIntrinsic', 'OBCameraParam', 'OBCmdVersion', 'OBColorPoint', 'OBCommunicationType', 'OBCompressionMode', 'OBCompressionParams', 'OBConvertFormat', 'OBCoordinateSystemType', 'OBDCPowerState', 'OBDDONoiseRemovalType', 'OBDataTranState', 'OBDepthCroppingMode', 'OBDepthPrecisionLevel', 'OBDepthWorkMode', 'OBDepthWorkModeList', 'OBDepthWorkModeTag', 'OBDeviceAccessMode', 'OBDeviceDevelopmentMode', 'OBDeviceIpAddrConfig', 'OBDeviceSyncConfig', 'OBDeviceTemperature', 'OBDeviceTimestampResetConfig', 'OBDeviceType', 'OBEdgeNoiseRemovalFilterParams', 'OBEdgeNoiseRemovalType', 'OBError', 'OBException', 'OBExtrinsic', 'OBFileTranState', 'OBFilterConfigSchemaItem', 'OBFilterConfigValueType', 'OBFilterList', 'OBFloat3D', 'OBFloatPropertyRange', 'OBFormat', 'OBFrameAggregateOutputMode', 'OBFrameMetadataType', 'OBFrameType', 'OBGyroFullScaleRange', 'OBGyroIntrinsic', 'OBGyroSampleRate', 'OBGyroValue', 'OBHardwareDecimationConfig', 'OBHdrConfig', 'OBHoleFillingMode', 'OBIntPropertyRange', 'OBLiDARPoint', 'OBLiDARScanPoint', 'OBLiDARScanRate', 'OBLiDARSpherePoint', 'OBLogLevel', 'OBMediaState', 'OBMediaType', 'OBMultiDeviceSyncConfig', 'OBMultiDeviceSyncMode', 'OBNoiseRemovalFilterParams', 'OBPermissionType', 'OBPixelType', 'OBPlaybackStatus', 'OBPoint2f', 'OBPoint3f', 'OBPowerLineFreqMode', 'OBPresetResolutionConfig', 'OBPropertyID', 'OBPropertyItem', 'OBPropertyType', 'OBProtocolVersion', 'OBRect', 'OBRegionOfInterest', 'OBRotateDegreeType', 'OBSensorType', 'OBSequenceIdItem', 'OBSpatialAdvancedFilterParams', 'OBStatus', 'OBStreamType', 'OBSyncMode', 'OBTofExposureThresholdControl', 'OBTofFilterRange', 'OBUSBPowerState', 'OBUint16PropertyRange', 'OBUint8PropertyRange', 'OBUpgradeState', 'PAUSED', 'PLAYING', 'Pipeline', 'PlaybackDevice', 'PointCloudFilter', 'PointsFrame', 'PresetResolutionConfigList', 'RecordDevice', 'SAMPLE_RATE_100_HZ', 'SAMPLE_RATE_12_5_HZ', 'SAMPLE_RATE_16_KHZ', 'SAMPLE_RATE_1_5625_HZ', 'SAMPLE_RATE_1_KHZ', 'SAMPLE_RATE_200_HZ', 'SAMPLE_RATE_25_HZ', 'SAMPLE_RATE_2_KHZ', 'SAMPLE_RATE_32_KHZ', 'SAMPLE_RATE_3_125_HZ', 'SAMPLE_RATE_400_HZ', 'SAMPLE_RATE_4_KHZ', 'SAMPLE_RATE_500_HZ', 'SAMPLE_RATE_50_HZ', 'SAMPLE_RATE_6_25_HZ', 'SAMPLE_RATE_800_HZ', 'SAMPLE_RATE_8_KHZ', 'SAMPLE_RATE_UNKNOWN', 'STOPPED', 'Sensor', 'SensorList', 'SequenceIdFilter', 'SpatialAdvancedFilter', 'StreamProfile', 'StreamProfileList', 'TemporalFilter', 'ThresholdFilter', 'UNKNOWN', 'VideoFrame', 'VideoStreamProfile', 'get_version', 'pyorbbecsdk', 'save_lidar_point_cloud_to_ply', 'save_point_cloud_to_ply', 'transformation2dto2d', 'transformation2dto3d', 'transformation3dto2d', 'transformation3dto3d']
COUNT: OBPlaybackStatus  # value = <OBPlaybackStatus.COUNT: 4>
PAUSED: OBPlaybackStatus  # value = <OBPlaybackStatus.PAUSED: 2>
PLAYING: OBPlaybackStatus  # value = <OBPlaybackStatus.PLAYING: 1>
SAMPLE_RATE_100_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_100_HZ: 7>
SAMPLE_RATE_12_5_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_12_5_HZ: 4>
SAMPLE_RATE_16_KHZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_16_KHZ: 14>
SAMPLE_RATE_1_5625_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_1_5625_HZ: 1>
SAMPLE_RATE_1_KHZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_1_KHZ: 10>
SAMPLE_RATE_200_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_200_HZ: 8>
SAMPLE_RATE_25_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_25_HZ: 5>
SAMPLE_RATE_2_KHZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_2_KHZ: 11>
SAMPLE_RATE_32_KHZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_32_KHZ: 15>
SAMPLE_RATE_3_125_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_3_125_HZ: 2>
SAMPLE_RATE_400_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_400_HZ: 16>
SAMPLE_RATE_4_KHZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_4_KHZ: 12>
SAMPLE_RATE_500_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_500_HZ: 9>
SAMPLE_RATE_50_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_50_HZ: 6>
SAMPLE_RATE_6_25_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_6_25_HZ: 3>
SAMPLE_RATE_800_HZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_800_HZ: 17>
SAMPLE_RATE_8_KHZ: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_8_KHZ: 13>
SAMPLE_RATE_UNKNOWN: OBGyroSampleRate  # value = <OBGyroSampleRate.SAMPLE_RATE_UNKNOWN: 0>
STOPPED: OBPlaybackStatus  # value = <OBPlaybackStatus.STOPPED: 3>
UNKNOWN: OBPlaybackStatus  # value = <OBPlaybackStatus.UNKNOWN: 0>
