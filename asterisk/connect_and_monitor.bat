@echo off
echo ========================================
echo Подключение к Asterisk серверу
echo ========================================
echo.

REM Подключаемся к серверу и выполняем команды
ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep INVITE"

pause