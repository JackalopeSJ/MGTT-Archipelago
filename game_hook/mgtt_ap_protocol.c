#include "mgtt_ap_protocol.h"

void mgtt_ap_initialize(volatile MgttApProtocol *protocol) {
    unsigned index;
    protocol->version = MGTT_AP_PROTOCOL_VERSION;
    protocol->client_ready = 0;
    protocol->spin_permissions = 0;
    protocol->putter_ranges = 0;
    protocol->menu_gate_flags = 0;
    protocol->roster_permissions = 0;
    protocol->mode_permissions = 0;
    protocol->putting_difficulty_permissions = 0;
    protocol->notification_cooldown = 0;
    protocol->native_selected_mode = 0;
    protocol->native_course_trace = 0;
    protocol->tournament_permissions = 0;
    for (index = 0; index < MGTT_AP_LOCATION_BYTES; ++index) {
        protocol->location_bits[index] = 0;
    }
    protocol->active_notification_ptr = 0;
    for (index = 0; index < MGTT_ITEM_COUNT; ++index) {
        protocol->item_counts[index] = 0;
    }
    for (index = 0; index < sizeof(protocol->seed_fingerprint); ++index) {
        protocol->seed_fingerprint[index] = 0;
    }
    protocol->notification_write_sequence = 0;
    protocol->notification_read_sequence = 0;
    for (index = 0; index < sizeof(protocol->notifications); ++index) {
        ((volatile uint8_t *)protocol->notifications)[index] = 0;
    }
    protocol->magic[0] = 'M';
    protocol->magic[1] = 'G';
    protocol->magic[2] = 'A';
    protocol->magic[3] = 'P';
}

bool mgtt_ap_has_item(volatile MgttApProtocol *protocol, unsigned item_id) {
    if (item_id >= MGTT_ITEM_COUNT) {
        return false;
    }
    return protocol->item_counts[item_id] != 0;
}

void mgtt_ap_check_location(volatile MgttApProtocol *protocol, unsigned location_id) {
    if (location_id >= MGTT_LOCATION_COUNT) {
        return;
    }
    protocol->location_bits[location_id >> 3] |= (uint8_t)(1u << (location_id & 7));
}
