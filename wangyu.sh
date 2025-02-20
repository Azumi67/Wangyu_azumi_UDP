#!/bin/bash
apt update -y
apt install wget -y
wget -O /etc/logo2.sh https://github.com/Azumi67/UDP2RAW_FEC/raw/main/logo2.sh
chmod +x /etc/logo2.sh
if [ -f "wangyu.py" ]; then
    rm wangyu.py
fi
wget https://github.com/Azumi67/Wangyu_azumi_UDP/releases/download/cores/wangyu.py
python3 wangyu.py
