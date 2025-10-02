@echo off
echo ========================================
echo     Asterisk Monitor - Чистые Логи
echo ========================================
echo Показываются ТОЛЬКО реальные звонки
echo Весь спам автоматически отфильтрован
echo ========================================
echo.
echo Ожидание подключения...
echo.

ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep -v 'REGISTER' | grep -v 'netsock2' | grep -v 'authenticator_digest' | grep -v 'Failed to authenticate' | grep -v 'No matching endpoint found' | grep -E 'INVITE|livekit|VERBOSE|WARNING|ERROR|161.115|35.'"

pause