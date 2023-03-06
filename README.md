Cluster Validation
==================

Before installing HPE Data Fabric it is critically important to validate the
hardware and software that HPE Data Fabric will be dependent on.  Doing so
will verify that items like disks, CPUs and NICs are performing as
expected and the benchmark metric logged.  Doing so will also
verify that many of the basic OS configurations and packages are
in the required state and that state is also recorded in an output
log.

Please use the steps below to test CPU/RAM, disk, and networking
performance as well as to verify that your cluster meets HPE Data Fabric
installation requirements. Pre-install tests should be run before
installing HPE Data Fabric.  Post-install tests should be run after installing
the HPE Data Fabric software and configuring it.  Post-install tests 
help assure that the cluster is in good working order and ready 
to hand over to your production team.

Install clustershell (rpm available via EPEL) on a machine with
password-less ssh to all other cluster nodes.  If using a non-root
account, then non-root account must have password-less sudo rights
configured in /etc/sudoers.  Update the file
`/etc/clustershell/groups.d/local.cfg` or `/etc/clustershell/groups`
to include an entry for "all" matching a pattern or patterns of
host names in your cluster.
For example;

    all: node[0-10]

Verify clush works correctly by running:

    clush -a date

Compare results with:

    clush -ab date

Complete documentation for clush and clustershell can be found here:
http://clustershell.readthedocs.org/en/latest/tools/clush.html

If you don't find clustershell in EPEL, you may be able to download rpm here:
`http://mirror.math.princeton.edu/pub/epel/6/x86_64/clustershell-1.7.2-1.el6.noarch.rpm`

Next, download and extract the cluster-validation package with a command like this:

    curl -L -o cluster-validation.tgz http://github.com/MapRPS/cluster-validation/tarball/master

Extract with tar in /root or your home folder and rename the top level folder like this:  

    mv jbenninghoff-cluster-validation-* cluster-validation
    or
    mv cluster-validation-* cluster-validation

Copy the cluster-validation folder to all nodes in the cluster.  The
clush command simplifies this:

    clush -a --copy /path.../cluster-validation
    clush -Ba ls /path.../cluster-validation	# confirm that all nodes have the utilties

Step 1 : Gather Base Audit Information
--------------------------------------
Run cluster-audit.sh as root to verify that all nodes have met the
HPE Data Fabric installation requirements.  Run:

    cd /root/cluster-validation/
    pre-install/cluster-audit.sh | tee cluster-audit.log

Run those commands on the node where clush has been installed and
ssh configured to access all the cluster nodes.  Examine the log
for inconsistency among any nodes.  Do not proceed until all
inconsistencies have been resolved and all requirements such as
missing rpms, Java version, etc, have been met.  Please send the
output of the cluster-audit.log back to us.

	NOTE: cluster-audit.sh is designed for physical servers.   
	Virtual Instances in cloud environments (eg Amazon, Google, or
	OpenStack) may generate confusing responses to some specific
	commands (eg dmidecode).  In most cases, these anomolies are
	irrelevant.

Step 2 : Evaluate Network Interconnect Bandwidth
------------------------------------------------
Use the network test to validate network bandwidth.  This will take
about two minutes or so to run and produce output so be patient.
The script will use clush to collect the IP addresses of all the
nodes and split the set in half, using first half as servers and
the second half as clients.  The half1 and half2 arrays in the
network-test.sh script can be manually defined as well.  There are
command line options for sequential mode and to run iperf as well.
Run:

    cd /root/cluster-validation/
    pre-install/network-test.sh | tee network-test.log

Run those commands on the node where clush has been installed and
configured.  Expect about 90% of peak bandwidth for either 1GbE or
10GbE networks:

	1 GbE  ==>  ~115 MB/sec 
	10 GbE ==> ~1150 MB/sec

Step 3 : Evaluate Raw Memory Performance
----------------------------------------
Use the stream59 benchmark to test memory performance.  This test will take 
about a minute or so to run.  It can be executed in parallel on all
the cluster nodes with the clush command:

    cd /root/cluster-validation/
    clush -Ba "$PWD/pre-install/memory-test.sh | grep -e ^Func -e ^Triad" | tee memory-test.log

System memory bandwidth is determined by speed of DIMMs, number of
memory channels and to a lesser degree by CPU frequency.  Current
generation Xeon based servers with eight or more 1600MHz DIMMs can
deliver 70-80GB/sec Triad results. Previous generation Xeon cpus
(Westmere) can deliver ~40GB/sec Triad results.  You can look up
the CPU as shown by cluster-audit.sh, at http://ark.intel.com/.
The technical specifications for the CPU model will include the Max
Memory Bandwidth (per CPU socket).  Servers typically have two CPU
sockets, so doubling that Max Bandwidth shown will give you the Max
Memory Bandwidth for the server.  The measured Stream Triad result
from memory-test.log can then be compared to the Max Memory Bandwidth
of the server.  The Triad bandwidth  should be approximately 75-85%
of the Max Memory Bandwidth of the server.

Step 4 : Evaluate Raw Disk Performance
--------------------------------------
Use the iozone benchmark to test disk performance. This process 
is destructive to disks that are tested, so make sure that 
you have not installed HPE Data Fabric nor have any needed data on those 
spindles. The script as shipped will ONLY list out the disks to
be tested. When run with no arguments, this script outputs a 
list of unused disks.  After carefully examining this list, run 
again with --destroy as the argument ('disk-test.sh --destroy') 
to run the destructive IOzone tests on all unused disks.

The test can be run in parallel on all nodes with clush:

    cd /root/cluster-validation/
    clush -ab "$PWD/pre-install/disk-test.sh"
    clush -ab "$PWD/pre-install/summIOzone.sh"

Current generation (2012+) 7200 rpm SATA drives can report 100-150MB/sec
sequential read and write throughput.  SAS, SSD and NVMe drives can
report from 200MB/sec to nearly 2GB/sec for NVMe drives as measured
by sequential iozone or fio tests on the raw device.  By default,
the disk test only uses a 4GB data set size in order to finish
quickly.  Consider using a larger size to measure disk throughput
more thoroughly.  Doing so will typically require hours to run which
could be done overnight if your schedule allows.  For large numbers
of nodes and disks there is a summIOzone.sh script that can help
provide a summary of disk-test.sh output using clush.

    clush -ab /root/cluster-validation/pre-install/summIOzone.sh

Complete Pre-Installation Checks
--------------------------------
When all subsystem tests have passed and met expectations, there
is an example install script in the pre-install folder that can be
modified and used for a scripted install by experienced system
administrators.

   pre-install/mapr-install.sh -h

Otherwise, follow the instructions from the mapr web site:
http://maprdocs.mapr.com/home/install.html

Post Installation tests
--------------------------------
Post installation tests are in the post-install folder.  The primary 
tests are RWSpeedTest and TeraSort.  Scripts to run each are 
provided in the folder.  Read the scripts for additional info. These
scripts should all be run by the HPE Data Fabric service account, typically
'mapr'.  The tests should be rerun as a normal user account to
verify that normal accounts have no permission issues and can
achieve the same throughput.

1: Create the benchmarks volume
--------------------------------------
A script to create a benchmarks volume `mkBMvol.sh` is provided.
Be sure to create the benchmarks volume before running any of the
post install benchmarks.

2: Run MFS benchmark
--------------------------------------
A script to run a per node MFS benchmark is the first post-install
test to run on HPE Data Fabric. It is run on each cluster node using the script
post-install/runRWSpeedTest.sh.  It should be run on all nodes using clush:

   clush -ab post-install/runRWSpeedTest.sh |tee MFSbenchmark.log

The default values are a good place to start.  Use the -h option
to the script to see the available options.

3: Run DFSIO benchmark
--------------------------------------
DFSIO is a standard Hadoop benchmark to measure HDFS throughput.
The script to run the benchmark can be run like this:

   post-install/runDFSIO.sh |tee DFSIO.log

The metric is a per map task throughput (averaged).

4: Run TeraSort benchmark
--------------------------------------
TeraSort is a standard Hadoop benchmark to measure MapReduce
performance for a simple but common use case, sorting.
The script to run the benchmark can be run like this:

   post-install/runTeraGenSort.sh 

The script combines TeraGen and TeraSort and takes an argument which
is the number of reduce tasks per node. It creates its own log file.

    NOTE: The TeraSort benchmark (executed by runTeraGenSort.sh) will likely
    require tuning for each specific cluster.  At a minimum, pass integer
    arguments in powers of 2 (e.g. 4, 8, etc) to the script to increase the
    number of reduce tasks per node up to the maximum reduce slots available on
    your cluster.  Experiment with the -D options if you are an MR2 expert.

There are other tunings in the script to optimize TeraSort performance.

5: Run Spark TeraSort benchmark
--------------------------------------
There is an unoptimized version of TeraSort for Spark on github.
This script runs that benchmark and can be run like this:

   post-install/runSparkTeraGenSort.sh |tee SparkTeraSort.log

This script needs improvement.  It currently requires cores, memory
and executors to be modified in the script for specific cluster
sizes.


The post-install folder also contains a mapr-audit.sh script which
can be run to provide an audit log of the HPE Data Fabric configuration.  The
script contains a useful set of example maprcli commands. There are
also install, upgrade and un-install options to mapr-install.sh
that leverage clush to run quickly on an entire set of nodes or
cluster.  Some of the scripts will not run without editing, so read the
scripts carefully to understand how to edit them with site specific
info.  All scripts support the -h option to show help on usage.

/John Benninghoff
