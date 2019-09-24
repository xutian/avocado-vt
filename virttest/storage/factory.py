from virttest.storage.storage_pool import storage_pool
from virttest.storage.storage_volume import exception
from virttest.storage.utils import utils_misc


class StoragePoolFactory(object):
    pools = {}

    @classmethod
    def produce(cls, name, protocol, params):
        support_protocols = storage_pool.SUPPORTED_STORAGE_POOLS.keys()
        if protocol not in support_protocols:
            raise ValueError(
                "Unknown protocol '%s'! supported protocols are: %s" %
                (protocol, support_protocols))
        cls_storage_pool = storage_pool.SUPPORTED_STORAGE_POOLS.get(protocol)
        pool = cls_storage_pool(name, cls, params)
        cls.pools[name] = pool
        return pool

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

    @staticmethod
    def format_volume(vol):
        vol_fmt = vol.fmt.type
        if vol_fmt == "qcow2":
            return utils_misc.format_volume_to_qcow2(vol)
        elif vol_fmt == "luks":
            return utils_misc.format_volume_to_luks(vol)
        elif vol_fmt == "raw":
            return utils_misc.format_volume_to_raw(vol)
        else:
            raise exception.UnsupportedVolumeFormatException(vol_fmt)

    @staticmethod
    def allocate_volume(vol):
        return vol.storage_pool.accocate_volume(vol)

# class StorageVolumeFactory:
#
#    @classmethod
#    def produce(cls, sp, volume_name, test_params):
#
#        def _build_volume(_volume_name):
#            volume_params = test_params.object_params(_volume_name)
#            volume_fmt = volume_params.get("image_format", "raw")
#            sp_name = volume_params.get("storage_pool")
#            # Notes:
#            #     backing file not always in same storage pool
#            # so, get pool by pool name
#            if sp.name != sp_name:
#                sp = sp.pool_mgr.get_pool_by_name(sp_name)
#            sp.refresh()
#            vol = sp.get_volume_by_name(_volume_name)
#            if vol is None:
#                vol = storage_volume.StorageVolume(
#                    _volume_name, sp, test_params)
#                vol.fmt = cls.product_format(
#                    _volume_name, volume_fmt, test_params)
#                vol.protocol = cls.produce_protocol(
#                    _volume_name, sp, test_params)
#            else:
#                if vol.fmt is None:
#                    vol.fmt = cls.product_format(
#                        _volume_name, volume_fmt, test_params)
#                if vol.protocol is None:
#                    vol.protocol = cls.produce_protocol(
#                        _volume_name, sp, test_params)
#            backing = volume_params.get("backing")
#            if backing:
#                for _vol in _build_volume(backing):
#                    vol.backing = _vol
#            yield vol
#
#        volume = next(_build_volume(volume_name))
#        volume.pool.volumes[volume_name] = volume
#        return volume
#
#    @classmethod
#    def produce_protocol(cls, name, pool, params):
#        protocol = pool.protocol
#        if protocol not in volume_protocol.SUPPORTED_VOLUME_PROTOCOL:
#            raise exception.UnsupportedVolumeProtocolException(protocol)
#
#        protocol_cls = volume_protocol.SUPPORTED_VOLUME_PROTOCOL[protocol]
#        protocol_params = params.object_params(name)
#        return protocol_cls(name, pool, protocol_params)
#
#    @classmethod
#    def produce_format(cls, name, fmt, params):
#        if fmt not in volume_format.SUPPORTED_VOLUME_FORMAT.keys():
#            raise exception.UnsupportedVolumeFormatException(fmt)
#        fmt_cls = volume_format.SUPPORTED_VOLUME_FORMAT[fmt]
#        fmt_params = params.object_params(name)
#        fmt_obj = fmt_cls(name, fmt_params)
#
#        return fmt_obj
