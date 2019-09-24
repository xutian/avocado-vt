import os

import rados
from gluster import gfapi

import copy
from virttest import utils_disk
from virttest.storage.storage_volume import exception
from virttest.storage.storage_volume import storage_volume
from virttest.storage.storage_volume import volume_format
from virttest.storage.storage_volume import volume_protocol
from virttest.storage.utils import iscsicli
from virttest.storage.utils import utils_misc


class BasePool(object):
    protocol = "none"
    pool_base_dir = utils_misc.make_pool_base_dir(protocol)

    def __init__(self, name, mgr, params):
        self.root_dir = os.path.join(self.pool_base_dir, name)
        self.name = name
        self.volumes = dict()
        self.available = None
        self.params = params
        self.pool_mgr = mgr

    def create(self):
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def destroy(self):
        raise NotImplementedError

    def exists(self):
        return os.path.exists(self.root_dir)

    def remove(self):
        if self.exists():
            os.removedirs(self.root_dir)

    def list_volumes(self):
        return self.volumes.values()

    def list_volume_names(self):
        return self.volumes.keys()

    def get_volume_by_name(self, name):
        return self.volumes.get(name)

    def allocate_volume(self, vol):
        raise NotImplementedError

    def build_volume(self, volume_name, params=None):
        """Build StorageVolume object by params"""

        def _build_volume(_volume_name, test_params):
            volume_params = test_params.object_params(_volume_name)
            volume_fmt = volume_params.get("image_format", "raw")
            sp_name = volume_params.get("storage_pool")
            # Notes:
            #     backing file not always in same storage pool
            # so, get pool by pool name
            if self.name != sp_name:
                sp = self.pool_mgr.get_pool_by_name(sp_name)
            else:
                sp = self
            vol = sp.get_volume_by_name(_volume_name)
            if vol is None:
                vol = storage_volume.StorageVolume(_volume_name, sp, test_params)
                vol.fmt = self.produce_format(_volume_name, volume_fmt, volume_params)
                vol.protocol = self.produce_protocol(_volume_name, sp, volume_params)
            else:
                if vol.fmt is None:
                    vol.fmt = self.produce_format(_volume_name, volume_fmt, volume_params)
                if vol.protocol is None:
                    vol.protocol = self.produce_protocol(_volume_name, sp, volume_params)
            backing = volume_params.get("backing", None)
            if backing:
                vol.backing = _build_volume(backing, test_params)
            return vol    

        if params is None:
            params = self.params
        #volume = next(_build_volume(volume_name, params))
        volume = _build_volume(volume_name, params)
        volume.pool.volumes[volume_name] = volume
        return volume

    def build_all_volumes(self, params=None):
        volumes = list()
        if params is None:
            params = self.params
        for name in params.objects("images"):
            img_params = params.object_params(name)
            if img_params.get("storage_pool") == self.name:
                vol = self.build_volume(name, params)
                print("===============build all: %s" % vol.name )
                volumes.append(vol)
        return volumes

    def produce_protocol(self, volume_name, pool, params=None):
        if params is None:
            params = self.params
        protocol = pool.protocol
        if protocol not in volume_protocol.SUPPORTED_VOLUME_PROTOCOL:
            raise exception.UnsupportedVolumeProtocolException(protocol)

        protocol_cls = volume_protocol.SUPPORTED_VOLUME_PROTOCOL[protocol]
        protocol_params = params.object_params(volume_name)
        return protocol_cls(volume_name, pool, protocol_params)

    def produce_format(self, volume_name, fmt, params=None):
        if params is None:
            params = self.params
        if fmt not in volume_format.SUPPORTED_VOLUME_FORMAT.keys():
            raise exception.UnsupportedVolumeFormatException(fmt)
        fmt_cls = volume_format.SUPPORTED_VOLUME_FORMAT[fmt]
        fmt_params = params.object_params(volume_name)
        fmt_obj = fmt_cls(volume_name, fmt_params)

        return fmt_obj


class FilePool(BasePool):
    protocol = "file"
    pool_base_dir = utils_misc.make_pool_base_dir(protocol)

    def __init__(self, name, mgr, params):
        super(FilePool, self).__init__(name, mgr, params)
        self.path = params["path"]

    def create(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if os.path.exists(self.root_dir):
            os.remove(self.root_dir)
        os.symlink(self.path, self.root_dir)

    def refresh(self):
        exists_file = set(
            [vol.protocol.filename for vol in self.list_volumes() if vol.protocol])
        new_files = set(self.list_files()) - exists_file
        print("---------------------------new files: %s" % new_files)
        map(self.rebuild_volume, new_files)

    def rebuild_volume(self, filename):
        pass
        # name = os.path.basename(filename)
        # info = utils_misc.get_volume_info(filename)
        # backing = info.get("backing-filename")
        # params = copy.deepcopy(self.params)
        # new_params = utils_params.Params()
        # new_params["image_filename_%s" % name] = filename
        # new_params["storage_type_%s" % name] = self.protocol
        # new_params["image_format_%s" % name] = info.get("format", "raw")
        # new_params["storage_pool_%s" % name] = self.name
        # if backing:
        #    new_params["backing_%s" % name] = os.path.basename(backing)
        # params.update(new_params)
        # return self.build_volume(name, params)

    def destroy(self):
        self.remove()

    def list_files(self):
        return utils_misc.list_files(self.root_dir)


class GlusterPool(FilePool):
    protocol = "gluster"
    pool_base_dir = utils_misc.make_pool_base_dir(protocol)

    def __init__(self, name, mgr, params):
        super(GlusterPool, self).__init__(name, mgr, params)
        self.host = params["gluster_host"]
        self.dir_path = params["gluster_dir"]
        self.volume_name = params["gluster_volume"]
        self.debug = params.get("debug")
        self.logfile = params.get("logfile")
        self._volume = None

    def create(self):
        volume = gfapi.Volume(self.host, self.volume_name)
        volume.mount()
        volume.mkdir(self.dir_path)
        self._volume = volume

    def list_files(self):
        return utils_misc.list_files_in_gluster_volume(
            self._volume, self.dir_path)

    def destroy(self):
        if self._volume.mounted:
            self._volume.umount()


class IscsiDriectPool(FilePool):
    protocol = "iscsi"
    pool_base_dir = utils_misc.make_pool_base_dir(protocol)

    def __init__(self, name, mgr, params):
        super(IscsiDriectPool, self).__init__(name, mgr, params)
        portal = params.get("portal", "")
        if ":" in portal:
            self.host = portal.split(':')[0]
            self.port = portal.split(':')[1]

        else:
            self.host = params["iscsi_host"]
            self.port = params.get("iscsi_port", "3260")

        self.transport = params.get("transport", "tcp")
        self.portal = ":".join([self.host, self.port])
        self.initiator = params["iscsi_initiator"]
        self.target = params["iscsi_target"]
        self.user = params.get("iscsi_user")
        self.password_secret = params.get("iscsi_password_secret")
        self.header_digest = params.get("iscsi_header_digest")
        self.timeout = params.get("iscsi_timeout")
        self.cli = iscsicli.IscsiCli(
            self.host, self.port, self.initiator, self.target)

    def create(self):
        self.cli.login()

    def list_files(self):
        return map(str, self.cli.list_luns())

    def destroy(self):
        self.cli.logout()


class NfsPool(FilePool):
    protocol = "nfs"
    pool_base_dir = utils_misc.make_pool_base_dir(protocol)

    def __init__(self, name, mgr, params):
        super(NfsPool, self).__init__(name, mgr, params)
        self.dir_path = params["nfs_dir"]
        self.hostname = params["nfs_host"]
        self.src_dir = ":".join([params["nfs_host"], params["nfs_dir"]])
        self.user = params.get("nfs_user")
        self.group = params.get("nfs_group")
        self.tcp_sync_count = params.get("nfs_tcp_sync_count")
        self.readahead_size = params.get("nfs_readahead_size")
        self.page_cache_size = params.get("nfs_page_cache_size")
        self.debug = params.get("nfs_debug_level")

    def create(self):
        if not os.path.exists(self.root_dir):
            os.mkdir(self.root_dir)
        if not utils_disk.is_mount(self.src_dir, self.root_dir, self.protocol):
            utils_disk.umount(self.src_dir, self.root_dir, self.protocol)
        utils_disk.mount(self.src_dir, self.root_dir, self.protocol)

    def destroy(self):
        if utils_disk.is_mount(self.src_dir, self.root_dir, self.protocol):
            utils_disk.umount(self.src_dir, self.root_dir, self.protocol)


class RbdPool(FilePool):
    protocol = 'rbd'
    pool_base_dir = utils_misc.make_pool_base_dir(protocol)

    def __init__(self, name, mgr, params):
        super(RbdPool, self).__init__(name, mgr, params)
        self.host = params["rbd_host"]
        self.port = params("rbd_port")
        self.conf = params.get("rbd_conf")
        self.snapshot = params.get("rdb_snapshot")
        self.user = params.get("rdb_user")
        self.key_secret = params.get("rdb_key_secret")
        self.auth_client_required = params.get("rdb_auth_client_required")
        self._cluster = None

    def create(self):
        self._cluster = rados.Rados(conffile=self.conf)
        self._cluster.connect()

    def destroy(self):
        self._cluster.shutdown()

    def list_pools(self):
        return self._cluster.list_pools()

    def create_pool(self, pool_name):
        self._cluster.create_pool(pool_name)

    def delete_pool(self, pool_name):
        self._cluster.delete_pool(pool_name)


SUPPORTED_STORAGE_POOLS = {
    "file": FilePool,
    "nfs": NfsPool,
    "gluster": GlusterPool,
    "rbd": RbdPool,
    "iscsi": IscsiDriectPool
}
