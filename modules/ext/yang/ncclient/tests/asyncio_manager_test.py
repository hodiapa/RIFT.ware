#!/usr/bin/env python3

import asyncio
import argparse
import logging
import xmlrunner
import os
import sys
import unittest
import tempfile
import shutil

import lxml.etree as etree
import lxml.objectify
import ncclient.asyncio_manager

import netconf_test_tool

logger = logging.getLogger(__name__)


class AsyncNetconfToolTestCase(netconf_test_tool.NetconfToolTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.loop = None
        self.async_manager = None

    def start_netconf_tool(self):
        @asyncio.coroutine
        def start():
            logger.debug("Starting netconf tool jar: %s", self._netconf_tool_jar)
            self._netconf_tool_proc = yield from asyncio.subprocess.create_subprocess_shell(
                    self.test_tool_cmd,
                    loop=self.loop,
                    )
            logger.debug("Started netconf tool jar (pid: %s)", self._netconf_tool_proc.pid)

            while True:
                yield from asyncio.sleep(1, loop=self.loop)

                try:
                    yield from self.loop.create_connection(
                            lambda: asyncio.Protocol(),
                            self._netconf_tool_host,
                            self.NETCONF_TOOL_PORT
                            )
                    break
                except OSError as e:
                    logger.warning("Connection failed: %s", str(e))

        self.loop.run_until_complete(
                asyncio.wait_for(start(), timeout=10, loop=self.loop),
                    )

    def stop_netconf_tool(self):
        @asyncio.coroutine
        def wait():
            self._netconf_tool_proc.terminate()
            yield from self._netconf_tool_proc.wait()

        if self._netconf_tool_proc is not None:
            self.loop.run_until_complete(wait())
            self._netconf_tool_proc = None

    def connect_ssh(self):
        @asyncio.coroutine
        def asyncio_connect_ssh():
            host = self._netconf_tool_host
            port = self.NETCONF_TOOL_PORT
            logger.debug("Connecting to netconf tool SSH (%s:%s)", host, port)
            self.async_manager = yield from ncclient.asyncio_manager.asyncio_connect(
                loop=self.loop,
                host=host,
                port=port,
                username="admin",
                password="admin",
                allow_agent=False,
                look_for_keys=False,
                hostkey_verify=False,
                )

        self.loop.run_until_complete(asyncio_connect_ssh())
        self.assertTrue(self.async_manager.connected)

    def close_ssh(self):
        @asyncio.coroutine
        def asyncio_close_session():
            logger.debug("Attempting to close SSH session.")
            yield from self.async_manager.close_session()
            self.async_manager = None

        self.loop.run_until_complete(asyncio_close_session())

    def tearDown(self):
        super().tearDown()

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        super().setUp()


class TestConnect(AsyncNetconfToolTestCase):
    def test_single_connect(self):
        self.connect_ssh()
        self.close_ssh()

    def test_many_connect(self):
        for i in range(3):
            self.connect_ssh()
            self.close_ssh()


class TestBasic(AsyncNetconfToolTestCase):
    def setUp(self):
        super().setUp()
        self.connect_ssh()

    def tearDown(self):
        self.close_ssh()
        super().tearDown()

    def test_get_empty_config(self):
        @asyncio.coroutine
        def get_empty_config():
            return (yield from self.async_manager.get_config(source="running"))

        reply = self.loop.run_until_complete(get_empty_config())
        logger.debug("Got get_config reply: %s", reply)
        root = etree.fromstring(str(reply).encode('utf8'))

        self.assertTrue(root.tag.endswith("rpc-reply"))
        self.assertEqual(1, len(root))
        data_child = root[0]
        self.assertTrue(data_child.tag.endswith("data"))

    def test_merge_config(self):
        @asyncio.coroutine
        def merge_config():
            return (yield from self.async_manager.edit_config(
                    config=(
                    '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">'
                       '<cont><l>THIS IS CONTENT</l></cont>'
                    '</config>'
                    ),
                    target="running",
                    default_operation="merge",
                    ))

        @asyncio.coroutine
        def get_config():
            return (yield from self.async_manager.get_config(
                    source="running",
                    filter=('xpath', 'opendaylight-inventory:nodes/node/17830-sim-device/yang-ext:mount/')
                    ))


        merge_reply = self.loop.run_until_complete(merge_config())
        logger.debug("Got merge config reply: %s", merge_reply)

        get_config_reply = self.loop.run_until_complete(get_config())
        logger.debug("Got get_config reply: %s", get_config_reply)

        root = etree.fromstring(str(get_config_reply).encode('utf8'))
        first = root.find(".//l")
        self.assertEquals("THIS IS CONTENT", first.text.strip())

    def test_merge_many(self):
        @asyncio.coroutine
        def merge_config(letter):
            return (yield from self.async_manager.edit_config(
                    config=(
                    '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">'
                       '<cont><{letter}>THIS IS CONTENT</{letter}></cont>'.format(letter=letter) +
                    '</config>'
                    ),
                    target="running",
                    default_operation="merge",
                    ))

        import itertools
        merge_cos = [merge_config(letter) for letter in itertools.permutations(['l', 'm', 'n', 'o', 'p'])]
        self.loop.run_until_complete(asyncio.gather(*merge_cos, loop=self.loop))


def main(argv=sys.argv[1:]):
    logging.basicConfig(format='TEST %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--netconf-host')
    parser.add_argument('--netconf-tool-jar')
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args(argv)
    if args.netconf_host is not None:
        AsyncNetconfToolTestCase.NETCONF_TOOL_HOST = args.netconf_host
    if args.netconf_tool_jar is not None:
        AsyncNetconfToolTestCase.NETCONF_TOOL_JAR = args.netconf_tool_jar

    # Set the global logging level
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.ERROR)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + args.unittest_args,
            testRunner=xmlrunner.XMLTestRunner(
                output=os.environ["RIFT_MODULE_TEST"]))

if __name__ == "__main__":
    main()
