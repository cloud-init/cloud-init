# This file is part of cloud-init. See LICENSE file for license information.

import pytest

from unittest import mock
from logging import Logger
from cloudinit.util import ProcessExecutionError
from cloudinit.config.cc_grub_dpkg import fetch_idevs, handle


class TestFetchIdevs:
    """Tests cc_grub_dpkg.fetch_idevs()"""

    # Note: udevadm info returns devices in a large single line string
    @pytest.mark.parametrize(
        "grub_output,path_exists,log_output,udevadm_output,expected_idevs",
        [
            # Inside a container, grub not installed
            (
                ProcessExecutionError(reason=FileNotFoundError()),
                False,
                'grub-common is not installed, e.g. inside a container',
                '',
                '',
            ),
            # Inside a container, grub installed
            (
                ProcessExecutionError(stderr="failed to get canonical path"),
                False,
                (
                    'Device mapping between /proc/self/mountinfo does not ',
                    'match /dev, e.g. inside a container'
                ),
                '',
                '',
            ),
            # KVM Instance
            (
                ['/dev/vda'],
                True,
                '',
                (
                    '/dev/disk/by-path/pci-0000:00:00.0 ',
                    '/dev/disk/by-path/virtio-pci-0000:00:00.0 '
                ),
                '/dev/vda',
            ),
            # Xen Instance
            (
                ['/dev/xvda'],
                True,
                '',
                '',
                '/dev/xvda',
            ),
            # NVMe Hardware Instance
            (
                ['/dev/nvme1n1'],
                True,
                '',
                (
                    '/dev/disk/by-id/nvme-Company_hash000 ',
                    '/dev/disk/by-id/nvme-nvme.000-000-000-000-000 ',
                    '/dev/disk/by-path/pci-0000:00:00.0-nvme-0 '
                ),
                '/dev/disk/by-id/nvme-Company_hash000',
            ),
            # SCSI Hardware Instance
            (
                ['/dev/sda'],
                True,
                '',
                (
                    '/dev/disk/by-id/company-user-1 ',
                    '/dev/disk/by-id/scsi-0Company_user-1 ',
                    '/dev/disk/by-path/pci-0000:00:00.0-scsi-0:0:0:0 '
                ),
                '/dev/disk/by-id/company-user-1',
            ),
        ],
    )
    @mock.patch("cloudinit.config.cc_grub_dpkg.util.logexc")
    @mock.patch("cloudinit.config.cc_grub_dpkg.os.path.exists")
    @mock.patch("cloudinit.config.cc_grub_dpkg.util.subp")
    def test_fetch_idevs(self, m_subp, m_exists, m_logexc, grub_output,
                         path_exists, log_output, udevadm_output,
                         expected_idevs):
        """Tests outputs from grub-probe and udevadm info against grub-dpkg"""
        m_subp.side_effect = [
            grub_output,
            ["".join(udevadm_output)]
        ]
        m_exists.return_value = path_exists
        log = mock.Mock(spec=Logger)
        idevs = fetch_idevs(log)
        assert expected_idevs == idevs
        if not path_exists:
            log.debug.assert_called_with("".join(log_output))


class TestHandle:
    """Tests cc_grub_dpkg.handle()"""

    @pytest.mark.parametrize(
        "cfg_idevs,cfg_idevs_empty,fetch_idevs_output,expected_log_output",
        [
            (
                # No configuration
                None,
                None,
                '/dev/disk/by-id/nvme-Company_hash000',
                (
                    "Setting grub debconf-set-selections with ",
                    "'/dev/disk/by-id/nvme-Company_hash000','false'"
                ),
            ),
            (
                # idevs set, idevs_empty unset
                '/dev/sda',
                None,
                '/dev/sda',
                (
                    "Setting grub debconf-set-selections with ",
                    "'/dev/sda','false'"
                ),
            ),
            (
                # idevs unset, idevs_empty set
                None,
                'true',
                '/dev/xvda',
                (
                    "Setting grub debconf-set-selections with ",
                    "'/dev/xvda','true'"
                ),
            ),
            (
                # idevs set, idevs_empty set
                '/dev/vda',
                'false',
                '/dev/disk/by-id/company-user-1',
                (
                    "Setting grub debconf-set-selections with ",
                    "'/dev/vda','false'"
                ),
            ),
            (
                # idevs set, idevs_empty set
                # Respect what the user defines, even if its logically wrong
                '/dev/nvme0n1',
                'true',
                '',
                (
                    "Setting grub debconf-set-selections with ",
                    "'/dev/nvme0n1','true'"
                ),
            )
        ],
    )
    @mock.patch("cloudinit.config.cc_grub_dpkg.fetch_idevs")
    @mock.patch("cloudinit.config.cc_grub_dpkg.util.get_cfg_option_str")
    @mock.patch("cloudinit.config.cc_grub_dpkg.util.logexc")
    @mock.patch("cloudinit.config.cc_grub_dpkg.util.subp")
    def test_handle(self, m_subp, m_logexc, m_get_cfg_str, m_fetch_idevs,
                    cfg_idevs, cfg_idevs_empty, fetch_idevs_output,
                    expected_log_output):
        """Test setting of correct debconf database entries"""
        m_get_cfg_str.side_effect = [
            cfg_idevs,
            cfg_idevs_empty
        ]
        m_fetch_idevs.return_value = fetch_idevs_output
        name = mock.Mock()
        cfg = mock.Mock()
        _cloud = mock.Mock()
        log = mock.Mock(spec=Logger)
        _args = mock.Mock()
        handle(name, cfg, _cloud, log, _args)
        log.debug.assert_called_with("".join(expected_log_output))


# vi: ts=4 expandtab