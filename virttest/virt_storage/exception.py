
class UnsupportedStoragePoolException(Exception):

    def __init__(self, sp_manager, sp_type):
        self.sp_manager = sp_manager
        self.sp_type = sp_type
        self.message = "Unsupported StoragePool type '%s', supported type are: %s" % (
            self.sp_type, sp_manager.SUPPORTED_STORAGE_POOLS.keys())

    def __str__(self):
        return "UnsupportedStoragePoolException:%s" % self.message


class UnsupportedVolumeFormatException(Exception):
    """"""

    def __init__(self, sp_manager, fmt):
        self.sp_manager = sp_manager
        self.fmt = fmt
        self.message = "Unsupported volume format '%s', supported format are: %s" % (
            self.fmt, sp_manager.SUPPORTED_VOLUME_FORMAT.keys())

    def __str__(self):
        return "UnsupportedVolumeFormatException:%s" % self.message


class UnsupportedVolumeProtocolException(Exception):
    """"""

    def __init__(self, sp_manager, protocol):
        self.sp_manager = sp_manager
        self.protocol = protocol
        self.message = "Unsupported volume protocol '%s', supported protocol are: %s" % (
            self.protocol, sp_manager.SUPPORTED_VOLUME_PROTOCOL.keys())

    def __str__(self):
        return "UnsupportedVolumeProtocolException:%s" % self.message
