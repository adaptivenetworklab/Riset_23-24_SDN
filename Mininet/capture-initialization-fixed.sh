upf1 tshark -i upf1-wlan0 -i eth0 -w /upf1-init -F pcapng -a duration:150 &
amf1 tshark -i amf1-wlan0 -i eth0 -w /amf1-init -F pcapng -a duration:150 &
gnb1 tshark -i gnb1-wlan0 -i eth0 -w /gnb1-init -F pcapng -a duration:150 &
gnb2 tshark -i gnb2-wlan0 -i eth0 -w /gnb2-init -F pcapng -a duration:150 &
ue1 tshark -i ue1-wlan0 -i eth0 -w /ue1-init -F pcapng -a duration:150 &
ue2 tshark -i ue2-wlan0 -i eth0 -w /ue2-init -F pcapng -a duration:150 &
ue3 tshark -i ue3-wlan0 -i eth0 -w /ue3-init -F pcapng -a duration:150 &
ue4 tshark -i ue4-wlan0 -i eth0 -w /ue4-init -F pcapng -a duration:150 &
ue5 tshark -i ue5-wlan0 -i eth0 -w /ue5-init -F pcapng -a duration:150 &
ue6 tshark -i ue6-wlan0 -i eth0 -w /ue6-init -F pcapng -a duration:150 &
