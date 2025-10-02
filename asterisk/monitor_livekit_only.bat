@echo off
echo ========================================
echo Мониторинг ТОЛЬКО LiveKit звонков
echo ========================================
echo Показываются запросы от LiveKit Cloud
echo ========================================
echo.

ssh -i C:\sshkeys\yc_ru_2025 ubuntu@51.250.74.43 -t "sudo tail -f /var/log/asterisk/full | grep -E 'livekit|161.115'"

pause