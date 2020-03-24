# This file is part of cloud-init. See LICENSE file for license information.

from cloudinit import log as logging
from cloudinit import util
import cloudinit.net.bsd

LOG = logging.getLogger(__name__)


class Renderer(cloudinit.net.bsd.BSDRenderer):

    def write_config(self):
        for device_name, v in self.interface_configurations.items():
            if_file = 'etc/hostname.%s' % device_name
            fn = util.target_path(self.target, if_file)
            content = 'dhcp\n'
            if isinstance(v, dict):
                content = "inet {address} {netmask}\n".format(
                            address=v.get('address'),
                            netmask=v.get('netmask'))
            util.write_file(fn, content)

    def start_services(self, run=False):
        if not self._postcmds:
            LOG.debug("netbsd generate postcmd disabled")
            return
        util.subp(['sh', '/etc/netstart'], capture=True)

    def set_route(self, network, netmask, gateway):
        if network == '0.0.0.0':
            if_file = 'etc/mygate'
            fn = util.target_path(self.target, if_file)
            content = gateway + '\n'
            util.write_file(fn, content)


def available(target=None):
    return util.is_OpenBSD()
