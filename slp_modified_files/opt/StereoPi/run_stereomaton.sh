#!/bin/sh

# copy config from /boot with replace windows \r symbols
mount /boot > /dev/null 2>&1
cat /boot/stereopi.conf | sed 's/\r$//' > /run/stereopi.conf

. ./config.conf

# check update file in /boot
UPDATE_FILENAME=`ls /boot/*.tar.gz 2>&1`
if [ "$?" = "0" ] ; then
    ./update.sh $UPDATE_FILENAME
fi


df /dev/mmcblk0p3 > /dev/null 2>&1
if [ "$?" != "0" ]; then
	echo "Record partion not found"
	echo "Creating new FAT32 partition"
	sudo echo -e "n\np\n3\n3932160\n\nt\n3\nc\nw\n" | fdisk /dev/mmcblk0
	reboot
else
	#sudo mkfs.vfat -F 32 /dev/mmcblk0p3 > /dev/null 2>&1

	sudo mount /dev/mmcblk0p3 /media > /dev/null 2>&1

	# check is partition already formatted
	if [ "$?" != "0" ]; then
		# format if not formatted
		sudo mkfs.vfat -F 32 /dev/mmcblk0p3 > /dev/null 2>&1
	fi
fi


sudo echo "powersave" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
sudo sysctl net.ipv4.udp_rmem_min=100000 >> /dev/null 2>&1
sudo sysctl net.ipv4.udp_wmem_min=100000 >> /dev/null 2>&1

#tvservice -e "CEA 4"

#killall -q fbi
#/usr/bin/fbi -d /dev/fb0 -a -fitwidth -noverbose -T 2  ./images/stereopi_bg2.jpg > /dev/null 2>&1

# start wlans manager
./scripts/wlan-switch.php &

./scripts/video-source.sh &
#./scripts/loop-rtsp.sh &
./scripts/loop-mpegts.sh &
./scripts/loop-mpegts-skybox.sh &
./scripts/loop-rtmp.sh &
./scripts/usb-video.sh &
./scripts/loop-record.sh &
./scripts/record-watcher.sh &
./scripts/loop-ws.sh &

cd ./skybox-server
./skybox-server.js &
cd ..

systemctl start pigpiod > /dev/null 2>&1
sysctl -w net.ipv6.conf.all.disable_ipv6=1

stereopi() {
	while [ 1 ] ; do
		./bin/stereopi
		sleep 1
	done
}
stereopi &

../stereomaton.py &

reconnect() {
	while true
	do
		if [ "1" -eq "$(cat /sys/class/net/wlan0/carrier)" ]
		then
			rsync -az /media/STEREOMATON/ haum@stereomaton-pc:/home/haum/STEREOMATON
			sleep 5
		else
			touch /run/wlan.update
			sleep 20
		fi
	done
}
reconnect &

server {
	cd /media/STEREOMATON
	python3 -m http.server --bind 0 8000
}
server &
