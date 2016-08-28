# Contest Preparation System

Download
--------
isolate is included using submodule  
For cloning use:
```bash
git clone --recursive
```
If you have already cloned CPS use:
```bash
git submodule update --init
```

Installation
------------
```bash
sudo apt-get install python3.5 python3.5-dev
```
- ### isolate installation
    create isolate user:
    ```bash
useradd isolate-user -c 'Isolate default user' -M -r -s /bin/false -U
usermod -a -G isolate-user YOUR_USER # replace YOUR_USER
```
    build isolate:
    ```bash
cd isolate
make isolate
chown root:isolate-user isolate
chmod 4750 isolate
```
