These files are added (or replaced) in SLP.

You might also need to add space on the partition and install a few packages:
```
mount -o remount,rw /
apt update
apt install python3-numpy
apt install python3-pip
pip3 install evdev
pip3 install pycairo
pip3 install opencv-python
apt install libcblas-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
```
