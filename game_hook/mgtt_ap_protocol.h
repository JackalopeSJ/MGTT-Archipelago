#ifndef MGTT_AP_PROTOCOL_H
#define MGTT_AP_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "mgtt_ap_ids.h"

#define MGTT_AP_PROTOCOL_VERSION 2
#define MGTT_AP_LOCATION_BYTES 0x28
#define MGTT_AP_NOTIFICATION_SLOTS 8
#define MGTT_AP_NOTIFICATION_SIZE 0x80

typedef struct {
    uint8_t magic[4];
    uint16_t version;
    uint8_t client_ready;
    uint8_t spin_permissions;
    uint8_t putter_ranges;
    uint8_t menu_gate_flags;
    uint16_t roster_permissions;
    uint16_t mode_permissions;
    uint8_t putting_difficulty_permissions;
    uint8_t notification_cooldown;
    uint8_t location_bits[MGTT_AP_LOCATION_BYTES];
    uint32_t active_notification_ptr;
    uint8_t reserved_3c[0x04];
    uint16_t item_counts[MGTT_ITEM_COUNT];
    uint8_t native_profile;
    uint8_t reserved_16f;
    uint16_t star_roster_permissions;
    uint8_t native_selected_mode;
    uint8_t native_course_trace;
    uint16_t tournament_permissions;
    uint8_t reserved_after_permissions[0x180 - 0x176];
    uint8_t seed_fingerprint[0x20];
    uint8_t reserved_1a0[0x60];
    uint32_t notification_write_sequence;
    uint32_t notification_read_sequence;
    uint8_t reserved_208[0x18];
    uint8_t notifications[MGTT_AP_NOTIFICATION_SLOTS][MGTT_AP_NOTIFICATION_SIZE];
} MgttApProtocol;

_Static_assert(offsetof(MgttApProtocol, location_bits) == 0x10, "location offset");
_Static_assert(offsetof(MgttApProtocol, client_ready) == 0x06, "ready offset");
_Static_assert(
    offsetof(MgttApProtocol, spin_permissions) == 0x07,
    "spin permission offset"
);
_Static_assert(
    offsetof(MgttApProtocol, putter_ranges) == 0x08,
    "putter range offset"
);
_Static_assert(
    offsetof(MgttApProtocol, notification_cooldown) == 0x0F,
    "notification cooldown offset"
);
_Static_assert(
    MGTT_AP_LOCATION_BYTES * 8 >= MGTT_LOCATION_COUNT,
    "location bitfield capacity"
);
_Static_assert(offsetof(MgttApProtocol, item_counts) == 0x40, "item offset");
_Static_assert(
    offsetof(MgttApProtocol, native_profile) == 0x16E,
    "native profile offset"
);
_Static_assert(
    offsetof(MgttApProtocol, star_roster_permissions) == 0x170,
    "star roster permission offset"
);
_Static_assert(
    offsetof(MgttApProtocol, tournament_permissions) == 0x174,
    "tournament permission offset"
);
_Static_assert(
    offsetof(MgttApProtocol, active_notification_ptr) == 0x38,
    "active notification pointer offset"
);
_Static_assert(offsetof(MgttApProtocol, seed_fingerprint) == 0x180, "seed offset");
_Static_assert(
    offsetof(MgttApProtocol, notification_write_sequence) == 0x200,
    "notification write offset"
);
_Static_assert(offsetof(MgttApProtocol, notifications) == 0x220, "notification offset");
_Static_assert(sizeof(MgttApProtocol) == 0x620, "protocol size");

void mgtt_ap_initialize(volatile MgttApProtocol *protocol);
bool mgtt_ap_has_item(volatile MgttApProtocol *protocol, unsigned item_id);
void mgtt_ap_check_location(volatile MgttApProtocol *protocol, unsigned location_id);

#endif
