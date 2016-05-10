netpd-server
============

If you're wondering what this is about, you might be more interested
to read about [netpd](http://www.netpd.org). If you really are
interested in running your own netpd-server, this is for you. 

__NOTE__: Please be aware that there is always an instance of the
netpd-server running on _netpd.org:3025_. You don't need to run this
yourself for joining a netpd session.

__netpd-server.pd__ is a Pd implementation of the protocol described in
<http://netpd.org/Protocol>. It acts as relay for OSC messages
sent to and from netpd clients.

#### How to run your own netpd-server ####

Make sure you have [Pure Data](http://msp.ucsd.edu/software.html) and the necessary 
libraries (a.k.a "externals") installed. To run this patch, you need the following
externals:
  * iemnet
  * osc
  * slip

As of Pd version 0.47 you can easily install externals through the menu 'Help'->'Find
externals'. Make sure to install the version suitable for your platform (listed in 
black color as opposed to grey color).

Once the necessary externals are installed, you can load netpd-server.pd with Pd.
Alternatively, you may want to launch Pd from the command-line in nogui-mode, since
the patch doesn't provide any way of user interaction:

`pd -nogui -open netpd-server.pd`

__NOTE__: netpd-server.pd might also work correctly with Pd-extended using the included
mrpeach library instead of the libraries from the list above. However, future support
for this setup is not guaranteed.

#### Bugs ####

Please report bugs to the author, either by mail to <roman@netpd.org> or opening
an issue on GitHub.
