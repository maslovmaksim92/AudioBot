@echo off
echo ========================================
echo   Asterisk Monitor - Только Звонки
echo ========================================
echo Весь спам отфильтрован
echo ========================================
echo.

ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep -v 'REGISTER' | grep -v 'endpoint_identifier_user' | grep -v 'netsock2' | grep -v 'authenticator_digest' | grep -v '37.49.225.223' | grep -v '198.23.190.62' | grep -v '20199' | grep -v '630' | grep -v '273' | grep -v '401' | grep -v '9100'"

pause