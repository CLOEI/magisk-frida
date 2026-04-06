#!/bin/sh
##########################################################################################
#
# Magisk Module Installer Script
#
##########################################################################################

##########################################################################################
# Config Flags
##########################################################################################

SKIPMOUNT=false
PROPFILE=false
POSTFSDATA=false
LATESTARTSERVICE=true

##########################################################################################
# Replace list
##########################################################################################

REPLACE="
"

[ ! -d $MODPATH/logs ] && mkdir -p $MODPATH/logs

# log
exec 2> $MODPATH/logs/custom.log
set -x

PATH=$PATH:/data/adb/ap/bin:/data/adb/magisk:/data/adb/ksu/bin

print_modname() {
  ui_print " "
  ui_print "    ********************************************"
  ui_print "    *          Magisk/KernelSU/APatch          *"
  ui_print "    *            Cheat Engine Server           *"
  ui_print "    ********************************************"
  ui_print " "
}

on_install() {
  case $ARCH in
    arm64) F_ARCH=$ARCH;;
    arm)   F_ARCH=$ARCH;;
    x86)   F_ARCH=$ARCH;;
    *)     ui_print "Unsupported architecture: $ARCH"; abort;;
  esac

  ui_print "- Detected architecture: $F_ARCH"

  if [ "$BOOTMODE" ] && [ "$KSU" ]; then
      ui_print "- Installing from KernelSU"
      ui_print "- KernelSU version: $KSU_KERNEL_VER_CODE (kernel) + $KSU_VER_CODE (ksud)"
  elif [ "$BOOTMODE" ] && [ "$APATCH" ]; then
      ui_print "- Installing from APatch"
      ui_print "- APatch version: $APATCH_VER_CODE. Magisk version: $MAGISK_VER_CODE"
  elif [ "$BOOTMODE" ] && [ "$MAGISK_VER_CODE" ]; then
      ui_print "- Installing from Magisk"
      ui_print "- Magisk version: $MAGISK_VER_CODE ($MAGISK_VER)"
  else
    ui_print "*********************************************************"
    ui_print "! Install from recovery is not supported"
    ui_print "! Please install from KernelSU or Magisk app"
    abort    "*********************************************************"
fi

  ui_print "- Unzipping module files..."
  F_TARGETDIR="$MODPATH/system/bin"
  mkdir -p "$F_TARGETDIR"
  chcon -R u:object_r:system_file:s0 "$F_TARGETDIR"
  chmod -R 755 "$F_TARGETDIR"

  busybox unzip -qq -o "$ZIPFILE" "files/ceserver-$F_ARCH" -d "$F_TARGETDIR"
  mv "$F_TARGETDIR/files/ceserver-$F_ARCH" "$F_TARGETDIR/ceserver"
  rmdir "$F_TARGETDIR/files"

  ui_print "- ceserver listens on port 52736"
  ui_print "- Forward port: adb forward tcp:52736 tcp:52736"
}

set_permissions() {
  # The following is the default rule, DO NOT remove
  set_perm_recursive $MODPATH 0 0 0755 0644

  # Custom permissions
  set_perm $MODPATH/system/bin/ceserver 0 2000 0755 u:object_r:system_file:s0
}

print_modname
on_install
set_permissions

[ -f $MODPATH/disable ] && {
  string="description=Run ceserver on boot: ❌ (failed)"
  sed -i "s/^description=.*/$string/g" $MODPATH/module.prop
}

#EOF
