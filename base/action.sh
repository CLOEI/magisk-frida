#!/system/bin/sh
MODPATH=${0%/*}
PATH=$PATH:/data/adb/ap/bin:/data/adb/magisk:/data/adb/ksu/bin

# log
exec 2> $MODPATH/logs/action.log
set -x

. $MODPATH/utils.sh

[ -f $MODPATH/disable ] && {
    echo "[-] ceserver is disabled"
    string="description=Run ceserver on boot: ❌ (failed)"
    sed -i "s/^description=.*/$string/g" $MODPATH/module.prop
    sleep 1
    exit 0
}

result="$(busybox pgrep 'ceserver')"
if [ $result -gt 0 ]; then
    echo "[-] Stopping ceserver..."
    busybox kill -9 $result
else
    echo "[-] Starting ceserver..."
    ceserver &
fi

sleep 1

check_ceserver_is_up 1

#EOF
