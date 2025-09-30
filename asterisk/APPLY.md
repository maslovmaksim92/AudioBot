# Apply VasDom Asterisk configs

1) SSH (Windows PowerShell):
   
   & "C:\\Windows\\System32\\OpenSSH\\ssh.exe" -i C:\\sshkeys\\yc_ru_2025 ubuntu@51.250.74.43

   sudo -s

2) pjsip.conf
   
   nano /etc/asterisk/pjsip.conf
   (paste contents from /app/asterisk/pjsip_working.conf)

3) extensions.conf
   
   nano /etc/asterisk/extensions.conf
   (paste contents from /app/asterisk/extensions_working.conf)

4) (Optional but recommended) quieter console
   
   cp /etc/asterisk/logger.conf /etc/asterisk/logger.conf.bak
   nano /etc/asterisk/logger.conf
   (paste contents from /app/asterisk/logger_quiet.conf)
   asterisk -rx "logger reload"

5) Restart Asterisk
   
   asterisk -rx "core restart now"

6) Quick test
   
   asterisk -rx "channel originate Local/8888@from-livekit application Wait 5"
   asterisk -rx "channel originate Local/79200924550@from-livekit application Wait 20"

Notes:
- Do not enable outbound_proxy in [novofon-endpoint]; it breaks R-URI and causes 484.
- Request-URI is forced by Dial(.../sip:${EXTEN}@sip.novofon.ru:5060,60).
- Codecs kept to alaw,ulaw for max compatibility.
