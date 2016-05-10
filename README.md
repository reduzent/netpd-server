netpd-server
============

If you're wondering what this is about, you might be more interested
to read about [netpd](http://www.netpd.org). If you really are
interested in running your own netpd-server, this is for you. 

__NOTE__:Please be aware that there is always an instance of this
netpd-server running on _netpd.org:3025_. You don't need to run this
yourself for joining a netpd session.

__netpd-server.pd__ is a Pd implementation of the protocol described in
<http://netpd.org/Protocol>. It acts as relay for OSC messages
sent to and from netpd clients.

### How to run your own netpd-server ###

Make sure you [Pure Data](http://msp.ucsd.edu/software.html) and the necessary 
libraries (a.k.a "externals") installed. To run this patch, you need the following
libraries:
  * iemnet
  * osc
  * slip

