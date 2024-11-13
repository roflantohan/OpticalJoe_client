# Setting for drone's simulator(SITL for Debian/Ubuntu)

Link: https://ardupilot.org/dev/docs/building-setup-linux.html#building-setup-linux

- Install Virtual Machine(VirtualBox) with Ubuntu distr.


Steps:

```
git clone --recursive https://github.com/ArduPilot/ardupilot.git
cd ardupilot
```

```
Tools/environment_install/install-prereqs-ubuntu.sh -y
```

```
. ~/.profile
```

```
./waf configure --board sitl
./waf plane
```

```
./Tools/autotest/sim_vehicle.py -v ArduPlane
```
