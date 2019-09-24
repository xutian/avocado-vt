from virttest.virt_storage import exception
from virttest.virt_storage import storage_pool
from virttest.virt_storage import storage_volume


class StoragePoolFactory(object):

    SUPPORTED_STORAGE_POOLS = {
        "file": storage_pool.FilePool,
        "nfs": storage_pool.NfsPool,
        "gluster": storage_pool.GlusterPool,
        "iscsi": storage_pool.IscsiDriectPool,
        "rbd": storage_pool.RbdPool
    }

    SUPPORTED_VOLUME_PROTOCOL = {
        "file": storage_volume.VolumeProtocolFile,
        "nfs": storage_volume.VolumeProtocolNfs,
        "iscsi": storage_volume.VolumeProtocolDirectIscsi,
        "gluster": storage_volume.VolumeProtocolGluster,
        "rbd": storage_volume.VolumeProtocolRbd
    }

    SUPPORTED_VOLUME_FORMAT = {
        "qcow2": storage_volume.Qcow2,
        "raw": storage_volume.Raw,
        "luks": storage_volume.Luks
    }

    pools = {}

    @classmethod
    def produce(cls, name, protocol, params):
        try:
            cls_storage_pool = cls.SUPPORTED_STORAGE_POOLS[protocol]
            pool = cls_storage_pool(name, cls, params)
            cls.pools[name] = pool
            return pool
        except KeyError:
            raise exception.UnsupportedStoragePoolException(cls, protocol)

    @classmethod
    def list_all_pools(cls):
        return cls.pools.values()

    @classmethod
    def get_pool_by_name(cls, name):
        return cls.pools.get(name)

    @classmethod
    def list_volumes(cls, pool_name):
        pool = cls.pools.get(pool_name)
        try:
            return pool.volumes.values()
        except AttributeError:
            pass
        return list()

    @classmethod
    def get_volume_by_name(cls, sp_name, vol_name):
        pool = cls.get_pool_by_name(sp_name)
        try:
            return pool.volumes.get(vol_name)
        except AttributeError:
            pass
        return None
