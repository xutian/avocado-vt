import os


class StorageVolume(object):

    def __init__(self, name, pool, params):
        self.name = name
        self.params = params
        self.protocol = None
        self.fmt = None
        self.pool = pool
        self.backing = None


class Luks(object):
    fmt = "luks"

    def __init__(self, name, params):
        self.key_secret_id = params.get("key_secret_id")
        self.key_secret_data = params.get("key_secret_data")


class Qcow2(object):
    fmt = "qcow2"

    def __init__(self, name, params):
        self.name = name
        self.lazy_refcounts = params.get("lazy_refcounts")
        self.pass_discard_request = params.get("pass_discard_request")
        self.pass_discard_snapshot = params.get("pass_discard_snapshot")
        self.pass_discard_other = params.get("pass_discard_other")
        self.overlap_check = params.get("overlap_check")
        self.cache_size = params.get("cache_size")
        self.l2_cache_size = params.get("l2_cache_size")
        self.l2_cache_entry_size = params.get("l2_cache_entry_size")
        self.refcount_cache_size = params.get("refcount_cache_size")
        self.cache_clean_interval = params.get("cache_clean_interval")
        self.encrypt = params.get("encrypt")
        self.data_file = params.get("data_file")
        self.file = None


class Raw(object):
    fmt = "raw"

    def __init__(self, name, params):
        self.name = name
        self.size = params.get("size")
        self.off = params.get("offset")


class VolumeProtocol(object):

    def __init__(self, name, pool, params):
        self.name = name
        self.pool = pool
        self.discard = params.get("discard")
        self.cache_direct = params.get("cache_direct")
        self.cache_no_flush = params.get("cache_no_flush")
        self.read_only = params.get("readonly")
        self.auto_read_only = params.get("auto_readonly")
        self.force_share = params.get("force_share")
        self.detect_zeroes = params.get("detect_zeroes")


class VolumeProtocolFile(VolumeProtocol):

    def __init__(self, name, pool, params):
        super(VolumeProtocolFile, self).__init__(name, pool, params)
        filename = params["image_filename"]
        self.filename = os.path.realpath(filename)


class VolumeProtocolGluster(VolumeProtocol):
    protocol = "gluster"

    def __init__(self, name, pool, params):
        super(VolumeProtocolGluster, self).__init__(name, pool, params)
        self.image_name = params["gluster_image_name"]


class VolumeProtocolDirectIscsi(VolumeProtocol):

    def __init__(self, name, pool, params):
        super(VolumeProtocolDirectIscsi, self).__init__(name, pool, params)
        self.lun = params.get("iscsi_lun", 0)


class VolumeProtocolNfs(VolumeProtocol):

    def __init__(self, name, pool, params):
        super(VolumeProtocolNfs, self).__init__(name, pool, params)
        self.image_name = params["nfs_image_name"]


class VolumeProtocolRbd(VolumeProtocol):

    def __init__(self, name, pool, params):
        super(VolumeProtocolRbd, self).__init__(name, pool, params)
        self.image_name = params["rbd_image_name"]
