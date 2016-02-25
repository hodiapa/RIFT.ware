
# 
# (c) Copyright RIFT.io, 2013-2016, All Rights Reserved
#

import asyncio
import logging
import os

from gi.repository import (
    RwVnsYang,
    RwDts as rwdts,
    RwTypes,
    ProtobufC,
)

import rift.tasklets

from rift.vlmgr import (
    VlrDtsHandler,
    VldDtsHandler,
    VirtualLinkRecord,
)

from rift.topmgr import (
    NwtopStaticDtsHandler,
    NwtopDiscoveryDtsHandler,
    NwtopDataStore,
    SdnAccountMgr,
)


class SdnInterfaceError(Exception):
    """ SDN interface creation Error """
    pass


class SdnPluginError(Exception):
    """ SDN plugin creation Error """
    pass


class VlRecordError(Exception):
    """ Vlr Record creation Error """
    pass


class VlRecordNotFound(Exception):
    """ Vlr Record not found"""
    pass

class SdnAccountExistsError(Exception):
    pass


class SDNAccountDtsHandler(object):
    XPATH = "C,/rw-sdn:sdn-account"

    def __init__(self, dts, log, parent):
        self._dts = dts
        self._log = log
        self._parent = parent

        self._sdn_account = {}

    def _set_sdn_account(self, account):
        self._log.info("Setting sdn account: {}".format(account))
        if account.name in self._sdn_account:
            self._log.error("SDN Account with name %s already exists. Ignoring config", account.name);
        self._sdn_account[account.name]  = account
        self._parent._acctmgr.set_sdn_account(account)

    @asyncio.coroutine
    def register(self):
        def apply_config(dts, acg, xact, action, _):
            self._log.debug("Got sdn account apply config (xact: %s) (action: %s)", xact, action)
            if action == rwdts.AppconfAction.INSTALL and xact.id is None:
                self._log.debug("No xact handle.  Skipping apply config")
                return RwTypes.RwStatus.SUCCESS

            return RwTypes.RwStatus.SUCCESS

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg):
            """ Prepare callback from DTS for SDN Account config """

            self._log.info("SDN Cloud account config received: %s", msg)

            fref = ProtobufC.FieldReference.alloc()
            fref.goto_whole_message(msg.to_pbcm())

            if fref.is_field_deleted():
                # Delete an NSD record
                self._log.warning("Deleting sdn account not yet supported")
            else:
                if msg.name in self._sdn_account:
                    msg = "Cannot update a SDN account that already was set."
                    self._log.error(msg)
                    raise SdnAccountExistsError(msg)

                # Set the sdn account record
                self._set_sdn_account(msg)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)


        self._log.debug("Registering for Sdn Account config using xpath: %s",
                        SDNAccountDtsHandler.XPATH,
                        )

        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        )

        with self._dts.appconf_group_create(acg_handler) as acg:
            acg.register(
                    xpath=SDNAccountDtsHandler.XPATH,
                    flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY,
                    on_prepare=on_prepare
                    )


class VnsManager(object):
    """ The Virtual Network Service Manager """
    def __init__(self, dts, log, log_hdl, loop):
        self._dts = dts
        self._log = log
        self._log_hdl = log_hdl
        self._loop = loop
        self._vlr_handler = VlrDtsHandler(dts, log, loop, self)
        self._vld_handler = VldDtsHandler(dts, log, loop, self)
        self._sdn_handler = SDNAccountDtsHandler(dts,log,self)
        self._acctmgr = SdnAccountMgr(self._log, self._log_hdl, self._loop)
        self._nwtopdata_store = NwtopDataStore(log)
        self._nwtopdiscovery_handler = NwtopDiscoveryDtsHandler(dts, log, loop, self._acctmgr, self._nwtopdata_store)
        self._nwtopstatic_handler = NwtopStaticDtsHandler(dts, log, loop, self._acctmgr, self._nwtopdata_store)

        self._log.info("type %s", type(self._log))

        self._vlrs = {}

    @asyncio.coroutine
    def register_vlr_handler(self):
        """ Register vlr DTS handler """
        self._log.debug("Registering  DTS VLR handler")
        yield from self._vlr_handler.register()

    @asyncio.coroutine
    def register_vld_handler(self):
        """ Register vlr DTS handler """
        self._log.debug("Registering  DTS VLD handler")
        yield from self._vld_handler.register()

    @asyncio.coroutine
    def register_sdn_handler(self):
        """ Register vlr DTS handler """
        self._log.debug("Registering  SDN Account config handler")
        yield from self._sdn_handler.register()

    @asyncio.coroutine
    def register_nwtopstatic_handler(self):
        """ Register static NW topology DTS handler """
        self._log.debug("Registering  static DTS NW topology handler")
        yield from self._nwtopstatic_handler.register()

    @asyncio.coroutine
    def register_nwtopdiscovery_handler(self):
        """ Register discovery-based NW topology DTS handler """
        self._log.debug("Registering  discovery-based DTS NW topology handler")
        yield from self._nwtopdiscovery_handler.register()

    @asyncio.coroutine
    def register(self):
        """ Register all static DTS handlers"""
        yield from self.register_sdn_handler()
        yield from self.register_vlr_handler()
        yield from self.register_vld_handler()
        yield from self.register_nwtopstatic_handler()
        # Not used for now
        yield from self.register_nwtopdiscovery_handler()

    def create_vlr(self, msg):
        """ Create VLR """
        if msg.id in self._vlrs:
            err = "Vlr id %s already exists" % msg.id
            self._log.error(err)
            raise VlRecordError(err)

        self._log.info("Creating VirtualLinkRecord %s", msg.id)
        self._vlrs[msg.id] = VirtualLinkRecord(self._dts,
                                               self._log,
                                               self._loop,
                                               self,
                                               msg,
                                               )
        return self._vlrs[msg.id]

    def get_vlr(self, vlr_id):
        """  Get VLR by vlr id """
        return self._vlrs[vlr_id]

    @asyncio.coroutine
    def delete_vlr(self, vlr_id, xact):
        """ Delete VLR with the passed id"""
        if vlr_id not in self._vlrs:
            err = "Delete Failed - Vlr id %s not found" % vlr_id
            self._log.error(err)
            raise VlRecordNotFound(err)

        self._log.info("Deleting virtual link id %s", vlr_id)
        yield from self._vlrs[vlr_id].terminate(xact)
        del self._vlrs[vlr_id]
        self._log.info("Deleted virtual link id %s", vlr_id)

    def find_vlr_by_vld_id(self, vld_id):
        """ Find a VLR matching the VLD Id """
        for vlr in self._vlrs.values():
            if vlr.vld_id == vld_id:
                return vlr
        return None

    @asyncio.coroutine
    def run(self):
        """ Run this VNSM instance """
        self._log.debug("Run VNSManager - registering static DTS handlers")
        yield from self.register()

    def vld_in_use(self, vld_id):
        """ Is this VLD in use """
        return False

    @asyncio.coroutine
    def publish_vlr(self, xact, path, msg):
        """ Publish a VLR """
        self._log.debug("Publish vlr called with path %s, msg %s",
                        path, msg)
        yield from self._vlr_handler.update(xact, path, msg)

    @asyncio.coroutine
    def unpublish_vlr(self, xact, path):
        """ Publish a VLR """
        self._log.debug("Unpublish vlr called with path %s", path)
        yield from self._vlr_handler.delete(xact, path)


class VnsTasklet(rift.tasklets.Tasklet):
    """ The VNS tasklet class """
    def __init__(self, *args, **kwargs):
        super(VnsTasklet, self).__init__(*args, **kwargs)
        
        #self.add_log_stderr_handler()
        self._dts = None
        self._vlr_handler = None

        self._vnsm = None
        # A mapping of instantiated vlr_id's to VirtualLinkRecord objects
        self._vlrs = {}

    def start(self):
        super(VnsTasklet, self).start()
        self.log.info("Starting VnsTasklet")

        self.log.debug("Registering with dts")
        self._dts = rift.tasklets.DTS(self.tasklet_info,
                                      RwVnsYang.get_schema(),
                                      self.loop,
                                      self.on_dts_state_change)

        self.log.debug("Created DTS Api GI Object: %s", self._dts)

    def on_instance_started(self):
        """ The task instance started callback"""
        self.log.debug("Got instance started callback")

    @asyncio.coroutine
    def init(self):
        """ task init callback"""
        self._vnsm = VnsManager(dts=self._dts,
                                log=self.log,
                                log_hdl=self.log_hdl,
                                loop=self.loop)
        yield from self._vnsm.run()

        # NSM needs to detect VLD deletion that has active VLR
        # self._vld_handler = VldDescriptorConfigDtsHandler(
        #         self._dts, self.log, self.loop, self._vlrs,
        #         )
        # yield from self._vld_handler.register()

    @asyncio.coroutine
    def run(self):
        """ tasklet run callback """
        pass

    @asyncio.coroutine
    def on_dts_state_change(self, state):
        """Take action according to current dts state to transition
        application into the corresponding application state

        Arguments
            state - current dts state
        """
        switch = {
            rwdts.State.INIT: rwdts.State.REGN_COMPLETE,
            rwdts.State.CONFIG: rwdts.State.RUN,
        }

        handlers = {
            rwdts.State.INIT: self.init,
            rwdts.State.RUN: self.run,
        }

        # Transition application to next state
        handler = handlers.get(state, None)
        if handler is not None:
            yield from handler()

        # Transition dts to next state
        next_state = switch.get(state, None)
        if next_state is not None:
            self._dts.handle.set_state(next_state)