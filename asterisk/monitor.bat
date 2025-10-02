@echo off
:start
cls
echo ========================================
echo   Asterisk Monitor - Автопереподключение
echo ========================================
echo Соединение разорвалось? Переподключаюсь...
echo Для выхода нажмите Ctrl+C
echo ========================================
echo.

ssh -i C:\sshkeys\yc_ru_2025 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep -v 'REGISTER' | grep -v 'endpoint_identifier_user' | grep -v 'netsock2' | grep -v 'authenticator_digest' | grep -v '37.49.225.223' | grep -v '198.23.190.62' | grep -v '20199' | grep -v '630' | grep -v '273' | grep -v '401' | grep -v '9100'"

echo.
echo ========================================
echo Соединение прервано!
echo Переподключение через 3 секунды...
echo ========================================
timeout /t 3 /nobreak >nul
goto start