is_mf=$(cat /proc/sys/net/ipv4/tcp_mf)
is_xcp=$(cat /proc/sys/net/ipv4/tcp_xcp)
cong=$(cat /proc/sys/net/ipv4/tcp_congestion_control)
echo $is_mf
echo $is_xcp
echo $cong
sudo modprobe -r sch_mf &&
sudo modprobe sch_mf mf=$is_xcp &&
sudo dmesg -c > old.log &&
#port=0 means trace all ports. 
#full=1 => write log whenever receive an acknowledgement
#full=0 => write log only when Cwnd changes
#sudo modprobe tcp_probe port=0 full=0 bufsize=128 &&
#Single & because it's a background task
sudo chmod a+rwx -R /sys/kernel/debug/ &&
cd /sys/kernel/debug/tracing &&
echo 1 > events/tcp/tcp_probe/enable &&
echo "(sport == 8554 && snd_cwnd != \$cwnd)"  > events/tcp/tcp_probe/filter &&
#echo "(sport == 8554 && snd_cwnd != $cwnd)"  > events/tcp/tcp_probe/filter &&
#echo "(sport == 8554 && snd_cwnd =< 0)"  > events/tcp/tcp_probe/filter &&
#Single & because it's a background task
cat trace_pipe > /home/tamim/net-next/trace.data &
TCPCAP=$! &&
echo $TCPCAP &&
sudo chmod a+rwx -R *.data &&
sudo python router.py; 
cd /home/tamim/net-next/ &&
if [ $is_mf -eq '1' ] && [ $is_xcp -eq '0' ]
then
    sudo cat trace.data | grep -a '172.16.101.1:8554' > h1-im.data &&
    sudo cat trace.data | grep -a '172.16.103.1:8554' > h3-im.data &&
    sudo cat trace.data | grep -a '172.16.105.1:8554' > h5-im.data &&
    sudo cat /proc/net/mf_probe0 > backlog0-im.data
elif [ $is_xcp -eq '1' ]
then
    sudo cat trace.data | grep -a '172.16.101.1:8554' > h1-xcp.data &&
    sudo cat trace.data | grep -a '172.16.103.1:8554' > h3-xcp.data &&
    sudo cat trace.data | grep -a '172.16.105.1:8554' > h5-xcp.data &&
    sudo cat /proc/net/mf_probe0 > backlog0-xcp.data 
elif [ $cong = "cdg" ]
then
    sudo cat trace.data | grep -a '172.16.101.1:8554' > h1-cdg.data &&
    sudo cat trace.data | grep -a '172.16.103.1:8554' > h3-cdg.data &&
    sudo cat trace.data | grep -a '172.16.105.1:8554' > h5-cdg.data &&
    sudo cat /proc/net/mf_probe0 > backlog0-cdg.data 
#    sudo cat /proc/net/mf_probe0 > backlog-tcp.data
else
    sudo cat trace.data | grep -a '172.16.101.1:8554' > h1-inigo.data &&
    sudo cat trace.data | grep -a '172.16.103.1:8554' > h3-inigo.data &&
    sudo cat trace.data | grep -a '172.16.105.1:8554' > h5-inigo.data &&
    sudo cat /proc/net/mf_probe0 > backlog0-inigo.data 
fi

#sudo kill $TCPCAP &&
#sudo lsof | grep tcpprobe &&
#for pid in $(sudo lsof | grep tcpprobe | awk '{print $2}') ; do sudo kill $pid ; done &&
#sudo modprobe -r tcp_probe
