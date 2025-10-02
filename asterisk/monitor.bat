@echo off
echo ========================================
echo     Asterisk Monitor - ВСЕ события
echo ========================================
echo Убран ВЕСЬ спам, показываются ВСЕ звонки
echo ========================================
echo.
echo Ожидание подключения...
echo.

ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep -v 'REGISTER' | grep -v 'netsock2.c' | grep -v 'authenticator_digest.c' | grep -v '37.49.225.223' | grep -v '198.23.190.62'"

pause