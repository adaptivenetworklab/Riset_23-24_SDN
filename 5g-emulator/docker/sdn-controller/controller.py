from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
import json

sdn_instance_name = 'sdn_api'

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SDNController, {sdn_instance_name: self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Save datapath for later use
        self.datapaths[datapath.id] = datapath

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # Handle packet in events
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

class SDNController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SDNController, self).__init__(req, link, data, **config)
        self.sdn_app = data[sdn_instance_name]

    @route('sdn', '/topology', methods=['GET'])
    def get_topology(self, req, **kwargs):
        sdn_app = self.sdn_app
        body = json.dumps({
            'switches': len(sdn_app.datapaths),
            'mac_to_port': sdn_app.mac_to_port
        })
        return Response(content_type='application/json', body=body)

    @route('sdn', '/flow', methods=['POST'])
    def add_flow_rule(self, req, **kwargs):
        sdn_app = self.sdn_app

        try:
            new_entry = json.loads(req.body)
            dpid = int(new_entry['dpid'])

            if dpid not in sdn_app.datapaths:
                return Response(status=404, body=json.dumps({"error": "Switch not found"}))

            datapath = sdn_app.datapaths[dpid]
            parser = datapath.ofproto_parser

            priority = int(new_entry.get('priority', 1))

            # Create match
            match_fields = new_entry.get('match', {})
            match = parser.OFPMatch(**match_fields)

            # Create actions
            actions = []
            for action in new_entry.get('actions', []):
                if action['type'] == 'OUTPUT':
                    actions.append(parser.OFPActionOutput(int(action['port'])))

            # Add flow
            sdn_app.add_flow(datapath, priority, match, actions)

            return Response(content_type='application/json', 
                           body=json.dumps({"status": "success"}))

        except Exception as e:
            return Response(status=400, body=json.dumps({"error": str(e)}))
