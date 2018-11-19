#!/usr/bin/env bash
#
# TODO:
#
# Re-implement using the SSH module
# Document functionality / description
# Document functions
# Document REQURIED/OPTIONAL/EXPORTED variables
#

function grub::entries
{
  GRUB_ENTRIES=`awk -F\' ' /menuentry_id_option / {print $4}' /boot/grub/grub.cfg`
  export GRUB_ENTRIES
}

function grub::entries_list
{
  grub::entries

  INDEX=0
  echo "$GRUB_ENTRIES" | while read ENTRY; do
    echo "$INDEX $ENTRY"
    INDEX=`expr $INDEX + 1`
  done
}

function grub::reboot_match
{
  NEEDLE=$1
  if [ -z "$NEEDLE" ]; then
    echo "grub::reboot_match: No match-string provided."
    return 1
  fi

  DO_SUDO=$2
  if [ -z "$DO_SUDO" ]; then
    DO_SUDO=1
  fi

  grub-editenv list | grep "saved_entry"
  HAS_REQUIRED_OPTION=$?
  if [ $HAS_REQUIRED_OPTION -ne 0 ]; then
    echo "CRAP"
  fi

  RES=1
  FOUND=""

  # Search by looping over lines such that we can get the INDEX
  grub::entries
  INDEX=0
  echo "$GRUB_ENTRIES" | while read ENTRY; do
    MATCH=`echo "$ENTRY" | grep "$NEEDLE" | grep -v "upstart" | grep -v "recovery"`
    if [ $? -eq 0 ]; then
      RES=0
      FOUND=$MATCH
      break
    fi
    INDEX=`expr $INDEX + 1`
  done

  # Set the grub "next_entry"
  if [ $RES -eq 0 ]; then
    echo "grub::reboot_match: Found and setting entry($FOUND)"
    if [ $DO_SUDO -eq 1 ]; then
      sudo grub-reboot $FOUND
    else
      grub-reboot $FOUND
    fi
  else
    echo "grub::reboot_match: Could not find entry matching($NEEDLE)"
  fi

  return $RES
}

