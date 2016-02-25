import logging
import os
import shutil
import tempfile
import unittest

logger = logging.getLogger(__name__)


class NetconfToolTestCase(unittest.TestCase):
    NETCONF_TOOL_JAR = \
     "/usr/share/java/netconf-testtool-0.4.0-SNAPSHOT-executable.jar"
    NETCONF_TOOL_PORT = 17830
    NETCONF_TOOL_HOST = "127.0.0.1"
    NETCONF_TOOL_SCHEMA_SOURCE_DIR = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "schema_files",
            )

    def __init__(self, *args, **kwargs):
        super(NetconfToolTestCase, self).__init__(*args, **kwargs)
        self._netconf_tool_jar = NetconfToolTestCase.NETCONF_TOOL_JAR
        self._netconf_tool_host = NetconfToolTestCase.NETCONF_TOOL_HOST
        self._netconf_tool_proc = None
        self._yang_schema_dir = None

    @property
    def test_tool_cmd(self):
        return ("java -Xmx1G -XX:MaxPermSize=256M -jar " +
               "{} --ssh true ".format(self._netconf_tool_jar) +
               "--schemas-dir {}".format(self._yang_schema_dir))

    def _create_yang_schema_dir(self):
        test_schema_dir = tempfile.mkdtemp("ncclienttest_schema")
        self._yang_schema_dir = os.path.join(test_schema_dir, "schema_files")

        logger.debug("Creating ncclient test schema dir: %s", self._yang_schema_dir)
        shutil.copytree(
                NetconfToolTestCase.NETCONF_TOOL_SCHEMA_SOURCE_DIR,
                self._yang_schema_dir,
                )

    def start_netconf_tool(self):
        raise NotImplementedError()

    def stop_netconf_tool(self):
        raise NotImplementedError()

    def connect_ssh(self):
        raise NotImplementedError()

    def close_ssh(self):
        raise NotImplementedError()

    def setUp(self):
        self._create_yang_schema_dir()
        self.start_netconf_tool()

    def tearDown(self):
        self.stop_netconf_tool()
        if self._yang_schema_dir is not None:
            logger.debug("Removing test schema dir: %s", self._yang_schema_dir)
            shutil.rmtree(self._yang_schema_dir)

