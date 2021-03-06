#!/usr/bin/python

"""
linuxrouter.py: Example network with Linux IP router

This example converts a Node into a router using IP forwarding
already built into Linux.


##############################################################################
# Topology with two switches and two hosts with static routes
#
#       172.16.101.0/24         172.16.10.0/24         172.16.102.0./24
#  h1 ------------------- r1 ------------------ r2------- -------------h2
#    .1                .2   .2               .3   .2                 .1
#
#       172.16.103.0/24         172.16.10.0/24         172.16.104.0./24
#  h3 ------------------- r1 ------------------ r2------- -------------h4
#    .1                .2   .2               .3   .2                 .1
#       172.16.105.0/24         172.16.10.0/24         172.16.106.0./24
#  h5 ------------------- r1 ------------------ r2------- -------------h6
#    .1                .2   .2               .3   .2                 .1


	   h1             h4             h6           h8
	 .1|              |              |            |
	   |              |              |            |
	101|          104 |           106|         108|
	   |              |              |            |
	   |              |              |            |
	 .2|              |              |            |
	   |  10.0/24         11.0/24    |   12.0/24  |            
	  r1 -------------r2------------r3-----------r4
	   |.2         .3   .2        .3 | .2      .3 |
	 .2|              |              |            |
	   |              |              |            |
	103|          105 |           107|         102|
	   |              |              |            |
	 .1|              |              |            |
	   h3             h5             h7           h2

##############################################################################
"""


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.node import CPULimitedHost
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import sys
import time

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):	
        h1 = self.addHost( 'h1', ip='172.16.101.1/24', defaultRoute='via 172.16.101.2' )
        h2 = self.addHost( 'h2', ip='172.16.102.1/24', defaultRoute='via 172.16.102.2' )

        h3 = self.addHost( 'h3', ip='172.16.103.1/24', defaultRoute='via 172.16.103.2' )
        h4 = self.addHost( 'h4', ip='172.16.104.1/24', defaultRoute='via 172.16.104.2' )

        h5 = self.addHost( 'h5', ip='172.16.105.1/24', defaultRoute='via 172.16.105.2' )
        h6 = self.addHost( 'h6', ip='172.16.106.1/24', defaultRoute='via 172.16.106.2' )

        h7 = self.addHost( 'h7', ip='172.16.107.1/24', defaultRoute='via 172.16.107.2' )
        h8 = self.addHost( 'h8', ip='172.16.108.1/24', defaultRoute='via 172.16.108.2' )

        r1 = self.addNode( 'r1', cls=LinuxRouter, ip='172.16.101.2/24' )
        r2 = self.addNode( 'r2', cls=LinuxRouter, ip='172.16.104.2/24' )
        r3 = self.addNode( 'r3', cls=LinuxRouter, ip='172.16.106.2/24' )
        r4 = self.addNode( 'r4', cls=LinuxRouter, ip='172.16.108.2/24' )

        self.addLink( h1, r1, intfName2='r1-eth2', params2={ 'ip' : '172.16.101.2/24' })
        self.addLink( h4, r2, intfName2='r2-eth2', params2={ 'ip' : '172.16.104.2/24' })
        self.addLink( h6, r3, intfName2='r3-eth2', params2={ 'ip' : '172.16.106.2/24' })
        self.addLink( h8, r4, intfName2='r4-eth2', params2={ 'ip' : '172.16.108.2/24' })
#       Don't move the line. It doesn't work for some reason
        self.addLink( r1, r2, intfName1='r1-eth10', params1={ 'ip' : '172.16.10.2/24' }, intfName2='r2-eth11', params2={ 'ip' : '172.16.10.3/24' })
        self.addLink( r2, r3, intfName1='r2-eth10', params1={ 'ip' : '172.16.11.2/24' }, intfName2='r3-eth11', params2={ 'ip' : '172.16.11.3/24' })
        self.addLink( r3, r4, intfName1='r3-eth10', params1={ 'ip' : '172.16.12.2/24' }, intfName2='r4-eth11', params2={ 'ip' : '172.16.12.3/24' })


        self.addLink( h3, r1, intfName2='r1-eth3', params2={ 'ip' : '172.16.103.2/24' })
        self.addLink( h5, r2, intfName2='r2-eth3', params2={ 'ip' : '172.16.105.2/24' })
        self.addLink( h7, r3, intfName2='r3-eth3', params2={ 'ip' : '172.16.107.2/24' })
        self.addLink( h2, r4, intfName2='r4-eth3', params2={ 'ip' : '172.16.102.2/24' })

def main(cli=0):
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo, controller = None )
    net.start()

    isRTP = False

    queuing_del = '100ms'

    access_delay = '20ms'
    access_delay_var = '2ms'
    access_loss = '0.1%'
    #mbps = Mega Bytes per sec
    access_rate = '1024kbit' 

    bottleneck_delay = '20ms'
    bottleneck_delay_var = '3ms'
    bottleneck_loss = '0%' #'0.1%'
    #mbps = Mega Bytes per sec
    bottleneck_rate = '666kbit'#'2048' for avoiding congestion

    info( '*** Configuring routers:\n' )
#    net[ 'r1' ].cmd( 'ip neigh add 172.16.10.3 lladdr 2e:a9:cf:14:b4:6a dev r1-eth1' )
    net[ 'r1' ].cmd( 'ip route add 172.16.104/24 nexthop via 172.16.10.3' )
    net[ 'r1' ].cmd( 'ip route add 172.16.102/24 nexthop via 172.16.10.3' )

    net[ 'r2' ].cmd( 'ip route add 172.16.102/24 nexthop via 172.16.11.3' )
    net[ 'r2' ].cmd( 'ip route add 172.16.106/24 nexthop via 172.16.11.3' )
    net[ 'r2' ].cmd( 'ip route add 172.16.103/24 nexthop via 172.16.10.2' )
    net[ 'r2' ].cmd( 'ip route add 172.16.101/24 nexthop via 172.16.10.2' )

    net[ 'r3' ].cmd( 'ip route add 172.16.102/24 nexthop via 172.16.12.3' )
    net[ 'r3' ].cmd( 'ip route add 172.16.108/24 nexthop via 172.16.12.3' )
    net[ 'r3' ].cmd( 'ip route add 172.16.101/24 nexthop via 172.16.11.2' )
    net[ 'r3' ].cmd( 'ip route add 172.16.105/24 nexthop via 172.16.11.2' )

    net[ 'r4' ].cmd( 'ip route add 172.16.101/24 nexthop via 172.16.12.2' )
    net[ 'r4' ].cmd( 'ip route add 172.16.107/24 nexthop via 172.16.12.2' )

    info( '*** Routing Table on Router:\n' )
    info( net[ 'r1' ].cmd( 'route' ) )

#Connecting hosts to routers via access links
    hosts = ['h3', 'h4', 'h5', 'h6', 'h7', 'h8']
    for host in hosts:
	net[host].cmd( 'tc qdisc add dev {0}-eth0 root handle 1: tbf rate {1} latency {2} burst 1540'.format(host, access_rate, queuing_del))
	net[host].cmd( 'tc qdisc add dev {0}-eth0 parent 1:1 handle 10: netem delay {1} {2}'.format(host, access_delay, access_delay_var))
	net[host].cmd( 'tc qdisc add dev {0}-eth0 parent 10:  handle 101: fq'.format(host))

    hosts = ['h1', 'h2']
    for host in hosts:
	net[host].cmd( 'tc qdisc add dev {0}-eth0 root handle 1: tbf rate {1} latency {2} burst 1540'.format(host, access_rate, queuing_del))
	net[host].cmd( 'tc qdisc add dev {0}-eth0 parent 1:1 handle 10: netem delay {1} {2}'.format(host, '1ms', access_delay_var))
	net[host].cmd( 'tc qdisc add dev {0}-eth0 parent 10:  handle 101: fq'.format(host))

#Connecting routers to hosts via access links
    routers = ['r1', 'r2', 'r3', 'r4']
    ifs = ['eth2', 'eth3']
    for router in routers:
    	for inf in ifs:
		net[router].cmd( 'tc qdisc add dev {0}-{1} root handle 1: tbf rate {2} latency {3} burst 1540'.format(router, inf, access_rate, queuing_del))
		net[router].cmd( 'tc qdisc add dev {0}-{1} parent 1:1 handle 10: netem delay {2} {3}'.format(router, inf, access_delay, access_delay_var))

    net['r1'].cmd( 'tc qdisc change dev r1-eth2 parent 1:1 handle 10: netem delay 1ms 1ms')
    net['r2'].cmd( 'tc qdisc change dev r4-eth3 parent 1:1 handle 10: netem delay 1ms 1ms')


#Connecting routers to routers via bottleneck links
    for router in ['r1', 'r2', 'r3']:    	
	net[router].cmd( 'tc qdisc add dev {0}-eth10 root handle 1: mf'.format(router))
	net[router].cmd( 'tc qdisc add dev {0}-eth10 parent 1: handle 2: htb default 10'.format(router))
	net[router].cmd( 'tc class add dev {0}-eth10 parent 2: classid 2:1 htb rate {1}'.format(router, bottleneck_rate))
	net[router].cmd( 'tc class add dev {0}-eth10 parent 2:1 classid 2:10 htb rate {1}'.format(router, bottleneck_rate))
	net[router].cmd( 'tc qdisc add dev {0}-eth10 parent 2:10 handle 10: netem delay {1} {2} loss {3}'.format(router, bottleneck_delay, bottleneck_delay_var, bottleneck_loss))


    for router in ['r2', 'r3', 'r4']:    	
	net[router].cmd( 'tc qdisc add dev {0}-eth11 root handle 1: htb default 10'.format(router))
	net[router].cmd( 'tc class add dev {0}-eth11 parent 1: classid 1:1 htb rate {1}'.format(router, bottleneck_rate))
	net[router].cmd( 'tc class add dev {0}-eth11 parent 1:1 classid 1:10 htb rate {1}'.format(router, bottleneck_rate))
	net[router].cmd( 'tc qdisc add dev {0}-eth11 parent 1:10 handle 10: netem delay {1} {2}'.format(router, bottleneck_delay, bottleneck_delay_var))	    


    hosts = [net['h1'], net['h2']]
        
    if cli:
        net.iperf(hosts, seconds=30, l4Type='UDP', udpBw='160M')
        CLI( net )
    elif isRTP:
	net[ 'h1' ].cmd( 'sudo sh rtp-streamer.sh  172.16.102.1' )
	net[ 'h2' ].cmd( 'sudo sh rtp-streaming.sh' )
	net[ 'h3' ].cmd( 'sudo sh rtp-streamer.sh  172.16.104.1 &' )
	net[ 'h4' ].cmd( 'sh rtp-streaming.sh' )
	net[ 'h5' ].cmd( 'sudo sh rtp-streamer.sh  172.16.106.1 &' )
	net[ 'h6' ].cmd( 'sh rtp-streaming.sh' )
#	net[ 'r1' ].cmd( 'watch  -dc  tc -s qdisc show dev r1-eth1' )
        CLI( net )
    else:
	net[ 'h1' ].cmd( 'sudo ./streamer  172.16.101.1 &' )
	net[ 'h2' ].cmd( 'sh streaming.sh 172.16.101.1' )
	net[ 'h3' ].cmd( 'sudo ./streamer  172.16.103.1 &' )
	net[ 'h4' ].cmd( 'sh streaming.sh 172.16.103.1' )
	net[ 'h5' ].cmd( 'sudo ./streamer  172.16.105.1 &' )
	net[ 'h6' ].cmd( 'sh streaming.sh 172.16.105.1' )
	net[ 'h7' ].cmd( 'sudo ./streamer  172.16.107.1 &' )
	net[ 'h8' ].cmd( 'sh streaming.sh 172.16.107.1' )
#	net[ 'r1' ].cmd( 'watch  -dc  tc -s qdisc show dev r1-eth1' )
    
	CLI( net )

    net.stop()

if __name__ == '__main__':
    args = sys.argv
    setLogLevel( 'info' )
    cli = 0
    if "--cli" in args:
        cli = 1
    main(cli)
