# Improved-Dijkstra-s-Algorithm-Based-Load-Balancing-SDN-Application

Overview: The project extends the Dijkstra’s algorithm and considers not only the edge weights but also the node weights and bandwidth of each network link. We used python to develop our load balancer application, Restful APIs and networkx module to gather all the network information mininet to generate our network topology and testing tools like Iperf, ping and wireshark to compare our load balancer with the original load balancer of floodlight.

Introduction: At present, network traffic is growing fast and complex as enterprises need to purchase more equipment to handle this complex network. The online services like e-commerce, websites, and social networks frequently use multiple servers to get high reliability and accessibility. Network congestion and server overload are the serious problems faced by the enterprises network. IP services uses Open Shortest Path First(OSPF), the computation is based on Dijkstra's algorithm which calculates the shortest path within the network with disadvantage is only edge weights is considered which makes it less efficient. In our extended dijkstra's based load balancer we consider not only the edge weights but also the node weights and bandwidth.

Implementation details: 
  Infrastructure and Topology Setup:	One of the crucial part of the project was to choose a suitable topology for clear demonstration of load balancing. But even then we wanted to test our load balancing module with a more challenging infrastructure. So, we joined two different topologies created in two different mininet VMs with GRE tunnel and VxLAN tunnel. Here are the steps followed to create the mininet topology. 
  
  Step 1: Created the two topologies in two different mininet VMs by editing a custom topology python file. The python file was easy to edit as it contained straight forward API calls like addLink(), addHost(), addSwitch(). The function of each API was as expect congruent with their names. 
-- addLink() - This API was used to create a link between either two switches or one switch and one host. 
-- addHost() - This API was used to add hosts to the network. While adding a host, it was also possible to assign a static IP address to the host.
-- addSwitch() - This API was used to add a switch to the network. 
  
  Step 2. Then run the mininet command to create the topology from the custom python file. Mention the IP address of the floodlight VM in both the command for both the mininet topology creation. For us, the IP address of the Floodlight VM was 192.168.56.101 and the name of custom topology pyhton file in both the VMs is topology4.py. Following is the command to create the custom topology in both the mininet VMs. i.e. sudo mn --custom topology4.py --topo mytopo--controller=remote,ip=192.168.56.101,port=6653
  
  Step 3. Once both the VMs are connected to the Floodlight VM, the next step is to create a GRE tunnel and VxLAN tunnel to connect both the topologies. Here are the commands to do so: 
GRE tunnel - The IP address of Mininet_1 VM is 192.168.56.102 and of Mininet_2 VM is 192.168.56.103. The connection is established between s21 of Mininet_1 to s17 of the  Mininet_2. 
- sh ovs-vsctl add-port s21 hello2 -- set interface hello2 type=gre option:remote_ip=192.168.56.103
- sh ovs-vsctl add-port s17 hello2 -- set interface hello2 type=gre option:remote_ip=192.168.56.102
VxLAN tunnel - The IP address of Mininet_1 VM is 192.168.56.102 and of Mininet_2 VM is 192.168.56.103. The connection is established between s18 of Mininet_1 to s22 of the  Mininet_2.
- sh ovs-vsctl add-port s18 hello1 -- set interface hello1 type=vxlan option:remote_ip=192.168.56.103
- sh ovs-vsctl add-port s22 hello1 -- set interface hello1 type=vxlan option:remote_ip=192.168.56.10

Flow of implementation: We have implemented the load balancing module as an application which interacts with the controller through RESTful (Representational State Transfer) API calls to collect data about the underlying network. Following is a step by step process of development and testing we have followed:

-- First the Floodlight VM and both the Mininet VMs are started. Different static IP addresses are assigned to all the VMs. In our case the assigned IP addresses are:
Floodlight VM - 192.168.56.101
Mininet_1 VM - 192.168.56.102
Mininet_2 VM - 192.168.56.103
-- Then the desired topology is created in both the Mininet VMs and connected through GRE and VxLAN tunnels. 
-- The current state and data regarding the topology is collected in JSON format using the API interface provided by floodlight controller. 
-- Then meaningful data is extracted from the JSON data pool for further calculation
-- The meaningful data is provided to the routing module which calculates the shortest possible route from one host to another with the help of Dijkstra's algorithm. 
-- The routing module gives the list of shortest path from one host to another. 
-- Then the load balancing module will find out the path which has least transmission cost with help of either Bandwidth scheme or Node weight / Edge weight scheme.
-- The Flow creator module prepare a static flow rules.
-- The flow rules obtained from the Flow creator module is pushed into the routers using the API interface provided by floodlight controller.
-- At last we compare the results from three scenarios with help of Iperf test and Wireshark test:
Firstly, with inbuilt Dijkstra's algorithm 
Secondly, with Bandwidth scheme, and
Thirdly, with Node weight / Edge weight scheme

Implemented methods of load balancing: 
There are many methods and parameters that can be used to perform load balancing. But, through this project, we have tried to implement two different scheme of load balancing i.e Bandwidth scheme and Node weight / Edge weight scheme.

1.Bandwidth Scheme: In this scheme of load balancing we have successfully improved the routing performance of the network compared to the default load balancing module performance. We do so by adding all the transmission rates of all the output port of all the switches in a link  which gives the total end to end transmission rates (totalTx) of the shortest paths. Then we find the path with maximum totalTx which becomes the best current path. 

2.Node Weight / Edge Weight Scheme: In this scheme of load balancing we have successfully improved the routing performance of the network compared to the default load balancing module performance. Here I define terms which is very useful in this scheme. 
-- The Node weight is defined as the amount of time a switch takes to process a certain number of packets (i.e. Latency of switch). 
-- The Edge weight is defined as the amount of time a link takes to transmit a certain number of packets (i.e. Latency of links). 
-- Therefore, the End-to-End latency is equal to the sum of total Node weights and total Edge weights. Using these 



