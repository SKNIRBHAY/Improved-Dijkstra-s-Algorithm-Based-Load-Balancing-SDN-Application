#!/usr/bin/python

from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch
from mininet.topo import Topo

class fatTreeTopo(Topo):

    "Fat Tree Topology"

    def __init__(self):
        "Create Fat tree Topology"

        Topo.__init__(self)

        #Add hosts
        h5 = self.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None)
        h6 = self.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None)
        h7 = self.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None)
        h8 = self.addHost('h8', cls=Host, ip='10.0.0.8', defaultRoute=None)

        #Add switches
	s3 = self.addSwitch('s3', cls=OVSKernelSwitch)
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch)
        s11 = self.addSwitch('s11', cls=OVSKernelSwitch)
        s17 = self.addSwitch('s17', cls=OVSKernelSwitch) #Switch which is not connected to any hosts
        s22 = self.addSwitch('s22', cls=OVSKernelSwitch)

        #Add links
        self.addLink(h5, s3)
        self.addLink(h6, s3)
        self.addLink(h7, s4)
        self.addLink(h8, s4)
        self.addLink(s3, s11)
        self.addLink(s11, s4)
        self.addLink(s4, s22)
        self.addLink(s3, s22)
        self.addLink(s11, s17)

topos = { 'mytopo': (lambda: fatTreeTopo() ) }
