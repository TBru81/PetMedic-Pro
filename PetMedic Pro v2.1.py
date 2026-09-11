# ============================================================
# PetMedic Pro 2.1
# UOAlive Pet Healing Script
# Razor Enhanced Python
#
# Production release:
# - Add player-selectable Double Heal and Panic Cure behaviors
# - Preserve both validated behaviors as enabled by default
# - Save both behavior choices separately for each character
# - Align all behavior information arrows in a labeled right-side column
# - Hide behavior checkboxes outside Vet + Magery while preserving preferences
# - Add the Suite-standard per-character Transparency option
# - Place selectable behaviors before automatic Adaptive Magery information
# - Standardize the spacing before Transparency and clear its divider
# - Test border-only transparent backgrounds with black center tiles omitted
# - Use one continuous transparent surface without resize-art borders
# - Add a compact title-area grab handle to transparent gumps
# - Increase the transparent title-bar height to center the Suite title
# - Apply the 15-pixel section gap consistently throughout Options
#
# PetMedic Pro 2.0 production baseline:
# - Preserve every validated Dev 8 healing path and locked spell timing
# - Standardize all information pages on one compact scrollable Suite gump
# - Add an Adaptive Magery information page
# - Use the Suite yellow journal hue for Healing Method changes
# - Preserve Veterinary no-bandage pause and hybrid fallback to Magery
# - Remove unsupported Magery resource inference after isolated API testing
# - Allow UOAlive's visible native warning to report missing Magery resources
# - Apply the approved compact Options-gump geometry and information arrows
# - Refine the main-gump Pet and Method value spacing
# - Prefix every PetMedic-generated journal message with [PetMedic Pro]
# - Use Suite configuration yellow for successful pet-selection confirmation
# - Remove obsolete journal, artwork, hue, and Veterinary state remnants
# - Persist each character's selected pet and healing method between launches
# - Use player-centered pet-selection journal wording
# - Refresh a saved pet's displayed name after delayed login resolution
# ============================================================

import json
import os
import time


# -----------------------------
# VERSION
# -----------------------------
TOOL_NAME = "PetMedic Pro"
VERSION = "2.1"


# -----------------------------
# CONFIG
# -----------------------------
BANDAGE_ID = 0x0E21
BANDAGE_RANGE = 2

HEAL_CAST_DELAY = 500
GHEAL_CAST_DELAY = 1150
ARCHCURE_CAST_DELAY = 1150
TARGET_WAIT = 1500

LOOP_DELAY = 100
BANDAGE_REUSE_MS = 2450
POST_SPELL_PAUSE = 150

DOUBLE_HEAL_ENTER_PCT = 0.50
DOUBLE_HEAL_EXIT_PCT = 0.75
MAGERY_HEAL_SWITCH_PCT = 0.75

PANIC_POISON_PCT = 0.40
PANIC_POISON_BANDAGE_ROUNDS = 2

PET_SERIAL_SHARED_KEY = "petheal_pet_serial"
HEAL_METHOD_SHARED_KEY = "petmedic_heal_method"
SETTINGS_FILE = "PetMedicPro_Settings.json"

# Preserve the established numeric IDs so saved Dev 7 Veterinary/Magery
# selections remain backward compatible. Retired Chivalry IDs 1 and 4
# safely migrate to Vet + Magery at startup.
METHOD_VET_MAGE = 0
METHOD_VET_ONLY = 2
METHOD_MAGE_ONLY = 3

HEAL_METHOD_NAMES = {
    METHOD_VET_MAGE: "Vet + Magery",
    METHOD_VET_ONLY: "Veterinary",
    METHOD_MAGE_ONLY: "Magery",
}

# -----------------------------
# GUMP IDS / BUTTONS
# -----------------------------
MAIN_GUMP_ID = 880321
OPTIONS_GUMP_ID = 880322
DOUBLE_HEAL_INFO_GUMP_ID = 880323
PANIC_CURE_INFO_GUMP_ID = 880324
ADAPTIVE_MAGERY_INFO_GUMP_ID = 880325

GUMP_X = 50
GUMP_Y = 50

BTN_TARGET_PET = 1
BTN_OPTIONS = 2
BTN_TOGGLE_HEALING = 3

BTN_METHOD_VET_MAGE = 10
BTN_METHOD_VET_ONLY = 12
BTN_METHOD_MAGE_ONLY = 13

BTN_DOUBLE_HEAL_INFO = 30
BTN_PANIC_CURE_INFO = 31
BTN_ADAPTIVE_MAGERY_INFO = 32
BTN_TOGGLE_DOUBLE_HEAL = 33
BTN_TOGGLE_PANIC_CURE = 34
BTN_TOGGLE_TRANSPARENCY = 35
BTN_BACK = 40


# -----------------------------
# SUITE ARTWORK / HUES
# -----------------------------
ART_OUTER = 9270
ART_GOLD_PANEL = 2620
ART_ACTION = 4005
ART_ACTION_PRESSED = 4007
ART_BACK = 4014
ART_BACK_PRESSED = 4016
ART_ROUND = 2103
ART_OPTIONS = 2006
ART_OPTIONS_PRESSED = 2007
ART_CHECK_OFF = 210
ART_CHECK_ON = 211
ART_TRIANGLE_RIGHT = 5601

HUE_TEXT = 1152
HUE_RED = 33
HUE_GREEN = 63
HUE_BLUE = 90
HUE_JOURNAL_OPTION = 53
TITLE_ORNAMENT_HUE = 2498

TITLE_OPTICAL_SHIFT_X = -1


# -----------------------------
# STATE
# -----------------------------
last_bandage_time = 0
last_spell_time = 0
last_lowhp_action = "spell"

double_heal_mode = False
double_heal_enabled = True
panic_cure_enabled = True
transparency_enabled = False

pet_serial = None
pet_name = ""
heal_method = METHOD_VET_MAGE

main_gump_closed = False
active_child_gump = None

# Session-only soft pause. Fresh launches always begin active so the
# existing Razor hotkey workflow continues to function as a hard on/off.
healing_paused = False

poison_low_bandage_rounds = 0
last_poison_bandage_mark = 0

last_drawn_pet_name = None
last_drawn_pet_selected = None
last_drawn_method = None
last_drawn_paused = None
last_drawn_pet_available = None

# Journal-only range warning state. This never gates or suppresses healing.
out_of_range_spell_failures = 0
out_of_range_warning_sent = False

vet_resource_warning_active = False


# -----------------------------
# GENERAL HELPERS
# -----------------------------
def now_ms():
    return int(time.time() * 1000)


def safe_send_message(text, hue):
    try:
        Misc.SendMessage("[PetMedic Pro] " + text, hue)
    except:
        pass


# -----------------------------
# PERSISTENT SETTINGS
# -----------------------------
def read_shared_int(name, default_value=None):
    try:
        if Misc.CheckSharedValue(name):
            return int(Misc.ReadSharedValue(name))
    except:
        pass
    return default_value


def save_shared_int(name, value):
    try:
        Misc.SetSharedValue(name, int(value))
    except:
        pass


def script_dir():
    try:
        return os.path.dirname(__file__)
    except:
        return os.getcwd()


def settings_path():
    return os.path.join(script_dir(), SETTINGS_FILE)


def read_settings_file():
    try:
        with open(settings_path(), "r") as settings_handle:
            data = json.load(settings_handle)
            return data if isinstance(data, dict) else {}
    except:
        return {}


def write_settings_file(data):
    try:
        with open(settings_path(), "w") as settings_handle:
            json.dump(data, settings_handle, indent=2)
        return True
    except Exception as ex:
        safe_send_message(
            "Your healing settings could not be saved: " + str(ex),
            HUE_RED
        )
        return False


def player_settings_key():
    try:
        return str(int(Player.Serial))
    except:
        return "default"


def player_shared_key(name):
    return name + "_" + player_settings_key()


def read_player_settings():
    data = read_settings_file()
    characters = data.get("characters", {}) or {}
    profile = characters.get(player_settings_key(), {}) or {}
    return data, characters, profile


def write_player_settings(pet_value, method_value):
    data, characters, profile = read_player_settings()
    profile["pet_serial"] = int(pet_value) if pet_value is not None else 0
    profile["heal_method"] = int(method_value)
    profile["double_heal_enabled"] = bool(double_heal_enabled)
    profile["panic_cure_enabled"] = bool(panic_cure_enabled)
    profile["transparency_enabled"] = bool(transparency_enabled)
    characters[player_settings_key()] = profile
    data["characters"] = characters
    return write_settings_file(data)


def normalize_heal_method(value):
    try:
        value = int(value)
    except:
        return METHOD_VET_MAGE

    # Dev 7 compatibility: IDs 0, 2, and 3 are unchanged.
    if value in HEAL_METHOD_NAMES:
        return value

    # Retired Chivalry IDs 1 and 4 safely fall back to Vet + Magery.
    return METHOD_VET_MAGE


def get_saved_pet_serial():
    _, characters, profile = read_player_settings()

    if "pet_serial" in profile:
        try:
            saved = int(profile.get("pet_serial", 0) or 0)
            return saved if saved > 0 else None
        except:
            return None

    saved = read_shared_int(player_shared_key(PET_SERIAL_SHARED_KEY), None)
    if saved is not None:
        return saved

    # The old key was global. Allow it to seed only the first durable
    # character profile so another character cannot inherit the same pet.
    if not characters:
        return read_shared_int(PET_SERIAL_SHARED_KEY, None)
    return None


def save_pet_serial(serial):
    save_shared_int(player_shared_key(PET_SERIAL_SHARED_KEY), serial)
    write_player_settings(serial, heal_method)


def clear_saved_pet_serial():
    try:
        Misc.RemoveSharedValue(player_shared_key(PET_SERIAL_SHARED_KEY))
        Misc.RemoveSharedValue(PET_SERIAL_SHARED_KEY)
    except:
        pass
    write_player_settings(None, heal_method)


def get_saved_heal_method():
    _, characters, profile = read_player_settings()

    if "heal_method" in profile:
        return normalize_heal_method(profile.get("heal_method"))

    saved = read_shared_int(player_shared_key(HEAL_METHOD_SHARED_KEY), None)
    if saved is not None:
        return normalize_heal_method(saved)

    # The old key was global. Allow it to seed only the first durable
    # character profile so another character cannot inherit the same method.
    if not characters:
        return normalize_heal_method(
            read_shared_int(HEAL_METHOD_SHARED_KEY, METHOD_VET_MAGE)
        )
    return METHOD_VET_MAGE


def save_heal_method(value):
    save_shared_int(player_shared_key(HEAL_METHOD_SHARED_KEY), value)
    write_player_settings(pet_serial, normalize_heal_method(value))


def get_saved_behavior_setting(name, default_value=True):
    _, _, profile = read_player_settings()
    if name not in profile:
        return default_value
    try:
        return bool(profile.get(name))
    except:
        return default_value


def save_behavior_settings():
    write_player_settings(pet_serial, heal_method)


def add_gump_background(gd, width, height, panels):
    if not transparency_enabled:
        Gumps.AddBackground(gd, 0, 0, width, height, ART_OUTER)
        for panel_x, panel_y, panel_width, panel_height in panels:
            Gumps.AddBackground(
                gd, panel_x, panel_y,
                panel_width, panel_height,
                ART_GOLD_PANEL
            )
        return

    # A shallow real background behind the title gives ClassicUO an artwork
    # surface that can be grabbed to move the otherwise alpha-only gump.
    Gumps.AddBackground(gd, 0, 0, width, 40, ART_OUTER)

    # Everything below the title remains one continuous transparent surface.
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)


# -----------------------------
# HEAL METHOD HELPERS
# -----------------------------
def method_uses_vet():
    return heal_method in (
        METHOD_VET_MAGE,
        METHOD_VET_ONLY,
    )


def method_uses_magery():
    return heal_method in (
        METHOD_VET_MAGE,
        METHOD_MAGE_ONLY,
    )


def method_is_hybrid():
    return heal_method == METHOD_VET_MAGE


def method_label():
    return HEAL_METHOD_NAMES.get(heal_method, "Vet + Magery")


def set_heal_method(value):
    global heal_method

    if value not in HEAL_METHOD_NAMES:
        return

    if heal_method == value:
        return

    heal_method = value
    save_heal_method(heal_method)
    reset_double_heal_mode()
    reset_poison_panic_tracking()
    reset_resource_state()

    safe_send_message(
        "Healing method set to " + method_label() + ".",
        HUE_JOURNAL_OPTION
    )


# -----------------------------
# PET HELPERS
# -----------------------------
def distance_to_mobile(mob):
    if mob is None:
        return 999
    try:
        px = Player.Position.X
        py = Player.Position.Y
        mx = mob.Position.X
        my = mob.Position.Y
        return max(abs(px - mx), abs(py - my))
    except:
        return 999


def in_bandage_range(mob):
    return distance_to_mobile(mob) <= BANDAGE_RANGE


def get_bandages():
    try:
        return Items.FindByID(BANDAGE_ID, -1, Player.Backpack.Serial)
    except:
        return None


def has_bandages():
    return get_bandages() is not None


def pet_exists(mob):
    return mob is not None and mob.Serial != 0


def pet_is_valid(mob):
    if mob is None:
        return False
    try:
        if mob.Serial == 0:
            return False
        if mob.HitsMax <= 0:
            return False
    except:
        return False
    return True


def get_pet():
    if pet_serial is None:
        return None
    try:
        return Mobiles.FindBySerial(pet_serial)
    except:
        return None


def pet_health_pct(mob):
    try:
        if mob.HitsMax <= 0:
            return 1.0
        return float(mob.Hits) / float(mob.HitsMax)
    except:
        return 1.0


def pet_is_damaged(mob):
    try:
        return mob.Hits < mob.HitsMax
    except:
        return False


def pet_is_poisoned(mob):
    try:
        return mob.Poisoned
    except:
        return False


def pet_is_panic_poison_low(mob):
    return pet_health_pct(mob) <= PANIC_POISON_PCT


def can_bandage():
    if not vet_source_available():
        return False
    return (now_ms() - last_bandage_time) >= BANDAGE_REUSE_MS


def can_cast_spell():
    return (now_ms() - last_spell_time) >= 900


# -----------------------------
# SOURCE AVAILABILITY
# -----------------------------
def reset_resource_state():
    global vet_resource_warning_active
    vet_resource_warning_active = False


def pause_healing_for_resource(message):
    global healing_paused

    if healing_paused:
        return

    healing_paused = True

    try:
        Target.Cancel()
    except:
        pass

    reset_double_heal_mode()
    reset_poison_panic_tracking()
    safe_send_message(message, HUE_RED)


def vet_source_available():
    global vet_resource_warning_active

    available = has_bandages()

    if available:
        vet_resource_warning_active = False
        return True

    if method_uses_vet() and not vet_resource_warning_active:
        vet_resource_warning_active = True

        if method_is_hybrid():
            safe_send_message(
                "You have no bandages left. You continue tending your pet with healing magic.",
                HUE_RED
            )
        else:
            pause_healing_for_resource(
                "You have no bandages left. Healing has been paused until you are ready to resume."
            )

    return False


def magery_source_available():
    return method_uses_magery()


# -----------------------------
# DOUBLE HEAL
# -----------------------------
def reset_double_heal_mode():
    global double_heal_mode
    double_heal_mode = False


def update_double_heal_mode(mob):
    global double_heal_mode

    if not double_heal_enabled or not method_is_hybrid():
        double_heal_mode = False
        return False

    health_pct = pet_health_pct(mob)

    if not double_heal_mode:
        if health_pct <= DOUBLE_HEAL_ENTER_PCT:
            double_heal_mode = True
    else:
        if health_pct >= DOUBLE_HEAL_EXIT_PCT:
            double_heal_mode = False

    return double_heal_mode


# -----------------------------
# PANIC CURE TRACKING
# -----------------------------
def reset_poison_panic_tracking():
    global poison_low_bandage_rounds
    global last_poison_bandage_mark

    poison_low_bandage_rounds = 0
    last_poison_bandage_mark = 0


def update_poison_panic_tracking(mob):
    global poison_low_bandage_rounds
    global last_poison_bandage_mark

    if not panic_cure_enabled or not method_is_hybrid():
        reset_poison_panic_tracking()
        return
    if not vet_source_available():
        reset_poison_panic_tracking()
        return
    if not pet_is_poisoned(mob):
        reset_poison_panic_tracking()
        return
    if not pet_is_panic_poison_low(mob):
        reset_poison_panic_tracking()
        return
    if not in_bandage_range(mob):
        reset_poison_panic_tracking()
        return

    if (
        last_bandage_time > 0
        and last_bandage_time != last_poison_bandage_mark
        and now_ms() - last_bandage_time >= BANDAGE_REUSE_MS
    ):
        last_poison_bandage_mark = last_bandage_time
        poison_low_bandage_rounds += 1


def should_force_secondary_cure(mob):
    if not panic_cure_enabled or not method_is_hybrid():
        return False
    if not vet_source_available():
        return False
    if not pet_is_poisoned(mob):
        return False
    if not pet_is_panic_poison_low(mob):
        return False
    if not in_bandage_range(mob):
        return False

    return poison_low_bandage_rounds >= PANIC_POISON_BANDAGE_ROUNDS


# -----------------------------
# PET SELECTION
# -----------------------------
def set_pet(mob):
    global pet_serial, pet_name

    pet_serial = mob.Serial

    try:
        pet_name = str(mob.Name)
    except:
        pet_name = ""

    save_pet_serial(pet_serial)
    reset_double_heal_mode()
    reset_poison_panic_tracking()


def clear_current_pet(remove_saved=False):
    global pet_serial, pet_name

    pet_serial = None
    pet_name = ""

    if remove_saved:
        clear_saved_pet_serial()

    reset_double_heal_mode()
    reset_poison_panic_tracking()


def choose_pet():
    try:
        Target.Cancel()
    except:
        pass

    try:
        Target.ClearLast()
    except:
        pass

    safe_send_message("Choose the companion you wish to tend.", HUE_BLUE)

    try:
        serial = Target.PromptTarget("Select your pet")
    except:
        safe_send_message("You were unable to select that companion.", HUE_RED)
        return False

    try:
        if serial is None or int(serial) == 0:
            return False
        serial = int(serial)
    except:
        return False

    mob = Mobiles.FindBySerial(serial)

    if mob is None or not pet_is_valid(mob):
        safe_send_message("You cannot tend that target.", HUE_RED)
        return False

    set_pet(mob)
    safe_send_message("You prepare to tend " + pet_name + ".", HUE_JOURNAL_OPTION)
    return True


def load_saved_pet_without_prompt():
    saved = get_saved_pet_serial()

    if saved is None:
        clear_current_pet(False)
        return

    try:
        saved_pet = Mobiles.FindBySerial(saved)
    except:
        saved_pet = None

    if saved_pet is not None and pet_is_valid(saved_pet):
        set_pet(saved_pet)
    else:
        # Mounted, stabled, or otherwise unresolved pets keep their saved
        # serial so PetMedic can recognize the same companion when it returns.
        global pet_serial, pet_name
        pet_serial = saved
        pet_name = ""
        reset_double_heal_mode()
        reset_poison_panic_tracking()


def refresh_resolved_pet_name(mob):
    global pet_name

    if not pet_exists(mob):
        return

    try:
        resolved_name = str(mob.Name)
    except:
        return

    if resolved_name and resolved_name != pet_name:
        pet_name = resolved_name


# -----------------------------
# TITLE / UI HELPERS
# -----------------------------
def add_petmedic_title(gd, overall_width, y=10):
    # Exact Suite title rendering established by ChestLoot:
    # AddHtml + <big>, with the title treated as one centered visual group.
    # PetMedic uses red Pet / Medic, white ornament / Pro.
    pet_width = 27
    ornament_width = 15
    medic_width = 42
    pro_width = 23

    # Validated optical spacing keeps the title readable and balanced.
    gap_pet_to_ornament = 1
    gap_ornament_to_medic = 2
    gap_medic_to_pro = 4

    total_width = (
        pet_width
        + gap_pet_to_ornament
        + ornament_width
        + gap_ornament_to_medic
        + medic_width
        + gap_medic_to_pro
        + pro_width
    )

    x = int((overall_width - total_width) / 2) + TITLE_OPTICAL_SHIFT_X

    Gumps.AddHtml(
        gd, x, y, pet_width + 10, 26,
        "<basefont color=#FF0000><big>Pet</big></basefont>",
        False, False
    )

    ornament_x = x + pet_width + gap_pet_to_ornament
    Gumps.AddImage(gd, ornament_x, y + 3, ART_ROUND, TITLE_ORNAMENT_HUE)

    medic_x = ornament_x + ornament_width + gap_ornament_to_medic
    Gumps.AddHtml(
        gd, medic_x, y, medic_width + 10, 26,
        "<basefont color=#FF0000><big>Medic</big></basefont>",
        False, False
    )

    pro_x = medic_x + medic_width + gap_medic_to_pro
    Gumps.AddHtml(
        gd, pro_x, y, pro_width + 10, 26,
        "<basefont color=#FFFFFF><big>Pro</big></basefont>",
        False, False
    )


def add_section_header(gd, text, y, divider_width=236, text_width=220):
    Gumps.AddHtml(
        gd, 30, y, text_width, 20,
        "<BASEFONT COLOR=#FFFF00>" + text + "</BASEFONT>",
        False, False
    )
    Gumps.AddHtml(
        gd, 32, y + 20, divider_width, 12,
        "<BASEFONT COLOR=#0080FF>----------------------------------------------</BASEFONT>",
        False, False
    )


def close_gump(gump_id):
    try:
        Gumps.CloseGump(gump_id)
    except:
        pass


def close_all_petmedic_gumps():
    close_gump(MAIN_GUMP_ID)
    close_gump(OPTIONS_GUMP_ID)
    close_gump(DOUBLE_HEAL_INFO_GUMP_ID)
    close_gump(PANIC_CURE_INFO_GUMP_ID)
    close_gump(ADAPTIVE_MAGERY_INFO_GUMP_ID)


def current_pet_available():
    if pet_serial is None:
        return False
    return pet_exists(get_pet())


def compact_pet_name(name, max_width=111):
    # ClassicUO uses a proportional font. This lightweight estimator keeps
    # the main gump fixed-width while avoiding obvious right-edge overflow.
    narrow = " .,:;!|iIl'`"
    wide = "MW@#%&"

    def estimated_width(text):
        total = 0
        for char in text:
            if char in narrow:
                total += 3
            elif char in wide:
                total += 8
            else:
                total += 6
        return total

    if estimated_width(name) <= max_width:
        return name

    suffix = "..."
    trimmed = name
    while trimmed and estimated_width(trimmed + suffix) > max_width:
        trimmed = trimmed[:-1]
    return trimmed + suffix


def display_pet_name():
    if not has_selected_pet():
        return "No Pet Selected"
    if not current_pet_available():
        return "Pet Not Found"
    return compact_pet_name(pet_name)


def has_selected_pet():
    return pet_serial is not None


# -----------------------------
# MAIN GUMP
# -----------------------------
def draw_main_gump():
    global last_drawn_pet_name
    global last_drawn_pet_selected
    global last_drawn_method
    global last_drawn_paused
    global last_drawn_pet_available

    if main_gump_closed:
        return

    close_gump(MAIN_GUMP_ID)

    width = 204
    height = 252

    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    add_gump_background(
        gd, width, height,
        [(16, 32, 172, 111), (16, 151, 172, 85)]
    )

    add_petmedic_title(gd, width, 10)

    Gumps.AddLabel(gd, 30, 48, HUE_TEXT, "Pet:")
    Gumps.AddLabel(
        gd,
        59,
        48,
        HUE_GREEN if current_pet_available() else HUE_RED,
        display_pet_name()
    )

    Gumps.AddLabel(gd, 30, 74, HUE_TEXT, "Method:")
    Gumps.AddLabel(gd, 77, 74, HUE_GREEN, method_label())

    # Standard centered Options control. No overlaid text label.
    options_x = int(width / 2) - 31
    Gumps.AddButton(
        gd,
        options_x,
        107,
        ART_OPTIONS,
        ART_OPTIONS_PRESSED,
        BTN_OPTIONS,
        1,
        0
    )

    Gumps.AddButton(
        gd,
        26,
        164,
        ART_ACTION,
        ART_ACTION_PRESSED,
        BTN_TARGET_PET,
        1,
        0
    )
    Gumps.AddLabel(
        gd,
        60,
        166,
        HUE_GREEN,
        "Target Pet"
    )

    # Soft healing control. The label describes the action clicking performs.
    # Fresh launches always begin active, so the initial control is Pause Healing.
    Gumps.AddButton(
        gd,
        26,
        200,
        ART_ACTION,
        ART_ACTION_PRESSED,
        BTN_TOGGLE_HEALING,
        1,
        0
    )
    Gumps.AddLabel(
        gd,
        60,
        202,
        HUE_GREEN if healing_paused else HUE_RED,
        "Resume Healing" if healing_paused else "Pause Healing"
    )

    Gumps.SendGump(
        MAIN_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )

    last_drawn_pet_name = pet_name
    last_drawn_pet_selected = has_selected_pet()
    last_drawn_method = heal_method
    last_drawn_paused = healing_paused
    last_drawn_pet_available = current_pet_available()


# -----------------------------
# OPTIONS GUMP
# -----------------------------
def add_method_row(gd, row_y, button_id, method_value):
    selected = heal_method == method_value
    button_art = ART_CHECK_ON if selected else ART_CHECK_OFF

    # ChestLoot loot-category checkbox artwork. These rows are mutually
    # exclusive choices, so available unselected methods remain white.
    Gumps.AddButton(
        gd,
        34,
        row_y - 2,
        button_art,
        button_art,
        button_id,
        1,
        0
    )
    Gumps.AddLabel(
        gd,
        68,
        row_y,
        HUE_GREEN if selected else HUE_TEXT,
        HEAL_METHOD_NAMES.get(method_value, "Vet + Magery")
    )


def add_behavior_toggle_row(gd, row_y, button_id, label, enabled):
    available = method_is_hybrid()

    if available:
        button_art = ART_CHECK_ON if enabled else ART_CHECK_OFF
        Gumps.AddButton(
            gd, 34, row_y - 2,
            button_art, button_art,
            button_id, 1, 0
        )

    label_hue = HUE_GREEN if available and enabled else HUE_TEXT
    Gumps.AddLabel(gd, 68, row_y, label_hue, label)


def draw_options_gump():
    global active_child_gump
    active_child_gump = "options"

    close_gump(MAIN_GUMP_ID)
    close_gump(OPTIONS_GUMP_ID)
    close_gump(DOUBLE_HEAL_INFO_GUMP_ID)
    close_gump(PANIC_CURE_INFO_GUMP_ID)
    close_gump(ADAPTIVE_MAGERY_INFO_GUMP_ID)

    width = 240
    height = 434

    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    add_gump_background(
        gd, width, height,
        [(16, 32, 208, 333), (16, 373, 208, 45)]
    )

    add_petmedic_title(gd, width, 10)

    add_section_header(gd, "Healing Method", 48, 176, 180)

    add_method_row(gd, 89, BTN_METHOD_VET_MAGE, METHOD_VET_MAGE)
    add_method_row(gd, 112, BTN_METHOD_VET_ONLY, METHOD_VET_ONLY)
    add_method_row(gd, 135, BTN_METHOD_MAGE_ONLY, METHOD_MAGE_ONLY)

    add_section_header(gd, "Healing Behaviors", 170, 176, 180)
    Gumps.AddLabel(gd, 181, 170, HUE_TEXT, "(Info)")

    add_behavior_toggle_row(
        gd, 206, BTN_TOGGLE_DOUBLE_HEAL, "Double Heal", double_heal_enabled
    )
    Gumps.AddButton(
        gd, 190, 208,
        ART_TRIANGLE_RIGHT, ART_TRIANGLE_RIGHT,
        BTN_DOUBLE_HEAL_INFO, 1, 0
    )

    add_behavior_toggle_row(
        gd, 233, BTN_TOGGLE_PANIC_CURE, "Panic Cure", panic_cure_enabled
    )
    Gumps.AddButton(
        gd, 190, 235,
        ART_TRIANGLE_RIGHT, ART_TRIANGLE_RIGHT,
        BTN_PANIC_CURE_INFO, 1, 0
    )

    # Adaptive Magery is automatic, so it follows the selectable behaviors.
    Gumps.AddLabel(gd, 68, 260, HUE_TEXT, "Adaptive Magery")
    Gumps.AddButton(
        gd, 190, 262,
        ART_TRIANGLE_RIGHT, ART_TRIANGLE_RIGHT,
        BTN_ADAPTIVE_MAGERY_INFO, 1, 0
    )

    # Suite standard: Transparency is always the final Options section.
    add_section_header(gd, "Transparency", 295, 176, 180)
    transparency_art = ART_CHECK_ON if transparency_enabled else ART_CHECK_OFF
    Gumps.AddButton(
        gd, 34, 328,
        transparency_art, transparency_art,
        BTN_TOGGLE_TRANSPARENCY, 1, 0
    )
    Gumps.AddLabel(
        gd, 68, 330,
        HUE_GREEN if transparency_enabled else HUE_TEXT,
        "Transparent Gumps"
    )

    Gumps.AddButton(
        gd,
        34,
        384,
        ART_BACK,
        ART_BACK_PRESSED,
        BTN_BACK,
        1,
        0
    )
    Gumps.AddLabel(gd, 68, 386, HUE_BLUE, "Back")

    Gumps.SendGump(
        OPTIONS_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )


# -----------------------------
# INFO GUMPS
# -----------------------------
def draw_double_heal_info_gump():
    global active_child_gump
    active_child_gump = "double_heal_info"

    close_gump(OPTIONS_GUMP_ID)
    close_gump(DOUBLE_HEAL_INFO_GUMP_ID)

    width = 305
    height = 350

    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    add_gump_background(
        gd, width, height,
        [(16, 32, 273, 248), (16, 288, 273, 46)]
    )

    add_petmedic_title(gd, width, 10)
    add_section_header(gd, "Double Heal", 48, 241)

    info = (
        "<BASEFONT COLOR=#FFFFFF>"
        "When your pet falls to 50% health or lower, PetMedic activates both "
        "available healing sources.<BR><BR>"
        "Veterinary and Magery work together until "
        "your pet recovers to 75% health.<BR><BR>"
        "When enabled, Double Heal applies to Vet + Magery."
        "</BASEFONT>"
    )

    Gumps.AddHtml(gd, 34, 84, 237, 180, info, False, True)

    Gumps.AddButton(
        gd, 34, 299,
        ART_BACK, ART_BACK_PRESSED,
        BTN_BACK, 1, 0
    )
    Gumps.AddLabel(gd, 68, 301, HUE_BLUE, "Back")

    Gumps.SendGump(
        DOUBLE_HEAL_INFO_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )


def draw_panic_cure_info_gump():
    global active_child_gump
    active_child_gump = "panic_cure_info"

    close_gump(OPTIONS_GUMP_ID)
    close_gump(PANIC_CURE_INFO_GUMP_ID)

    width = 305
    height = 350

    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    add_gump_background(
        gd, width, height,
        [(16, 32, 273, 248), (16, 288, 273, 46)]
    )

    add_petmedic_title(gd, width, 10)
    add_section_header(gd, "Panic Cure", 48, 241)

    info = (
        "<BASEFONT COLOR=#FFFFFF>"
        "While your pet is within bandage range, Veterinary normally handles poison.<BR><BR>"
        "If your pet remains poisoned at 40% health or lower after two completed "
        "bandage attempts, PetMedic uses Arch Cure as emergency support.<BR><BR>"
        "Panic Cure ends when the poison clears.<BR><BR>"
        "When enabled, Panic Cure applies to Vet + Magery."
        "</BASEFONT>"
    )

    Gumps.AddHtml(gd, 34, 84, 237, 180, info, False, True)

    Gumps.AddButton(
        gd, 34, 299,
        ART_BACK, ART_BACK_PRESSED,
        BTN_BACK, 1, 0
    )
    Gumps.AddLabel(gd, 68, 301, HUE_BLUE, "Back")

    Gumps.SendGump(
        PANIC_CURE_INFO_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )


def draw_adaptive_magery_info_gump():
    global active_child_gump
    active_child_gump = "adaptive_magery_info"

    close_gump(OPTIONS_GUMP_ID)
    close_gump(ADAPTIVE_MAGERY_INFO_GUMP_ID)

    width = 305
    height = 350

    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    add_gump_background(
        gd, width, height,
        [(16, 32, 273, 248), (16, 288, 273, 46)]
    )

    add_petmedic_title(gd, width, 10)
    add_section_header(gd, "Adaptive Magery", 48, 241)

    info = (
        "<BASEFONT COLOR=#FFFFFF>"
        "Above 75% health, PetMedic uses Heal for a faster response and lower mana consumption.<BR><BR>"
        "At 75% health or lower, PetMedic uses Greater Heal for stronger recovery.<BR><BR>"
        "Adaptive Magery applies whenever Magery is active, either alone or alongside Veterinary."
        "</BASEFONT>"
    )

    Gumps.AddHtml(gd, 34, 84, 237, 180, info, False, True)

    Gumps.AddButton(
        gd, 34, 299,
        ART_BACK, ART_BACK_PRESSED,
        BTN_BACK, 1, 0
    )
    Gumps.AddLabel(gd, 68, 301, HUE_BLUE, "Back")

    Gumps.SendGump(
        ADAPTIVE_MAGERY_INFO_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )


# -----------------------------
# GUMP EVENT HANDLING
# -----------------------------
def should_redraw_main():
    return (
        pet_name != last_drawn_pet_name
        or has_selected_pet() != last_drawn_pet_selected
        or heal_method != last_drawn_method
        or healing_paused != last_drawn_paused
        or current_pet_available() != last_drawn_pet_available
    )


def handle_main_gump():
    global main_gump_closed
    global pet_serial
    global pet_name
    global healing_paused

    if main_gump_closed or active_child_gump is not None:
        return

    try:
        if not Gumps.WaitForGump(MAIN_GUMP_ID, 1):
            return
        response = Gumps.GetGumpData(MAIN_GUMP_ID)
        button_id = int(response.buttonid)
    except:
        return

    if button_id == 0:
        main_gump_closed = True
        close_all_petmedic_gumps()
        return

    if button_id == BTN_TARGET_PET:
        close_gump(MAIN_GUMP_ID)

        previous_serial = pet_serial
        previous_name = pet_name

        if not choose_pet():
            # Preserve the previous selection after a cancelled/invalid retarget.
            pet_serial = previous_serial
            pet_name = previous_name

        if not main_gump_closed:
            draw_main_gump()
        return

    if button_id == BTN_TOGGLE_HEALING:
        was_paused = healing_paused
        healing_paused = not healing_paused

        # A soft pause must release PetMedic's targeting control immediately.
        if healing_paused:
            try:
                Target.Cancel()
            except:
                pass
            reset_double_heal_mode()
            reset_poison_panic_tracking()
        elif was_paused:
            # Resource-depletion pauses never probe or restart automatically.
            # Manual Resume restores the selected method's sources for a fresh
            # attempt without changing the player's saved method.
            reset_resource_state()

        draw_main_gump()
        return

    if button_id == BTN_OPTIONS:
        draw_options_gump()


def handle_options_gump():
    global active_child_gump
    global double_heal_enabled
    global panic_cure_enabled
    global transparency_enabled

    if active_child_gump != "options":
        return

    try:
        if not Gumps.WaitForGump(OPTIONS_GUMP_ID, 1):
            return
        response = Gumps.GetGumpData(OPTIONS_GUMP_ID)
        button_id = int(response.buttonid)
    except:
        return

    if button_id == 0 or button_id == BTN_BACK:
        active_child_gump = None
        close_gump(OPTIONS_GUMP_ID)
        draw_main_gump()
        return

    method_buttons = {
        BTN_METHOD_VET_MAGE: METHOD_VET_MAGE,
        BTN_METHOD_VET_ONLY: METHOD_VET_ONLY,
        BTN_METHOD_MAGE_ONLY: METHOD_MAGE_ONLY,
    }

    if button_id in method_buttons:
        set_heal_method(method_buttons[button_id])
        draw_options_gump()
        return

    if button_id == BTN_TOGGLE_DOUBLE_HEAL:
        if not method_is_hybrid():
            draw_options_gump()
            return
        double_heal_enabled = not double_heal_enabled
        reset_double_heal_mode()
        save_behavior_settings()
        safe_send_message(
            "Double Heal is " + ("enabled." if double_heal_enabled else "disabled."),
            HUE_JOURNAL_OPTION
        )
        draw_options_gump()
        return

    if button_id == BTN_TOGGLE_PANIC_CURE:
        if not method_is_hybrid():
            draw_options_gump()
            return
        panic_cure_enabled = not panic_cure_enabled
        reset_poison_panic_tracking()
        save_behavior_settings()
        safe_send_message(
            "Panic Cure is " + ("enabled." if panic_cure_enabled else "disabled."),
            HUE_JOURNAL_OPTION
        )
        draw_options_gump()
        return

    if button_id == BTN_TOGGLE_TRANSPARENCY:
        transparency_enabled = not transparency_enabled
        save_behavior_settings()
        safe_send_message(
            "Transparency is " + ("enabled." if transparency_enabled else "disabled."),
            HUE_JOURNAL_OPTION
        )
        draw_options_gump()
        return

    if button_id == BTN_DOUBLE_HEAL_INFO:
        draw_double_heal_info_gump()
        return

    if button_id == BTN_PANIC_CURE_INFO:
        draw_panic_cure_info_gump()
        return

    if button_id == BTN_ADAPTIVE_MAGERY_INFO:
        draw_adaptive_magery_info_gump()
        return


def handle_info_gump(gump_id, child_name):
    if active_child_gump != child_name:
        return

    try:
        if not Gumps.WaitForGump(gump_id, 1):
            return
        response = Gumps.GetGumpData(gump_id)
        button_id = int(response.buttonid)
    except:
        return

    if button_id == 0 or button_id == BTN_BACK:
        close_gump(gump_id)
        draw_options_gump()


def handle_gumps():
    if active_child_gump == "options":
        handle_options_gump()
    elif active_child_gump == "double_heal_info":
        handle_info_gump(DOUBLE_HEAL_INFO_GUMP_ID, "double_heal_info")
    elif active_child_gump == "panic_cure_info":
        handle_info_gump(PANIC_CURE_INFO_GUMP_ID, "panic_cure_info")
    elif active_child_gump == "adaptive_magery_info":
        handle_info_gump(ADAPTIVE_MAGERY_INFO_GUMP_ID, "adaptive_magery_info")
    else:
        handle_main_gump()


# -----------------------------
# HEALING ACTIONS
# -----------------------------
def use_bandage_on_pet(mob):
    global last_bandage_time
    global last_lowhp_action

    bandage = get_bandages()
    if bandage is None:
        vet_source_available()
        return False

    if not in_bandage_range(mob):
        return False

    try:
        Items.UseItem(bandage)

        if Target.WaitForTarget(TARGET_WAIT, False):
            Target.TargetExecute(mob.Serial)
            last_bandage_time = now_ms()
            last_lowhp_action = "bandage"
            return True
    except:
        pass

    return False



def capture_journal_cursor():
    """Return the latest Razor Enhanced JournalEntry for cursor-based reads."""
    try:
        entries = list(Journal.GetJournalEntry(-1) or [])
        if entries:
            return entries[-1]
    except:
        pass
    return None


def update_spell_range_warning(journal_cursor):
    """Escalate repeated native range failures without altering healing behavior."""
    global out_of_range_spell_failures
    global out_of_range_warning_sent

    too_far = False

    try:
        if journal_cursor is None:
            entries = list(Journal.GetJournalEntry(-1) or [])
        else:
            entries = list(Journal.GetJournalEntry(journal_cursor) or [])

        for entry in entries:
            try:
                if str(entry.Text).strip() == "That is too far away.":
                    too_far = True
                    break
            except:
                pass
    except:
        # Journal observation must never interfere with the healing path.
        return

    if too_far:
        out_of_range_spell_failures += 1

        if out_of_range_spell_failures >= 4 and not out_of_range_warning_sent:
            safe_send_message(
                "Your healing magic cannot reach your pet from this distance.",
                HUE_RED
            )
            out_of_range_warning_sent = True
    else:
        out_of_range_spell_failures = 0
        out_of_range_warning_sent = False


def cast_magery_on_pet(spell_name, mob, cast_delay):
    global last_spell_time
    global last_lowhp_action

    if not can_cast_spell() or not magery_source_available():
        return False

    try:
        Spells.CastMagery(spell_name)
        Misc.Pause(cast_delay)

        if Target.WaitForTarget(TARGET_WAIT, False):
            range_journal_cursor = capture_journal_cursor()
            Target.TargetExecute(mob.Serial)
            last_spell_time = now_ms()
            last_lowhp_action = "spell"
            Misc.Pause(POST_SPELL_PAUSE)
            update_spell_range_warning(range_journal_cursor)
            return True

    except:
        pass

    return False


def cast_heal_on_pet(mob):
    return cast_magery_on_pet("Heal", mob, HEAL_CAST_DELAY)


def cast_greater_heal_on_pet(mob):
    return cast_magery_on_pet("Greater Heal", mob, GHEAL_CAST_DELAY)


def cast_adaptive_magery_heal_on_pet(mob):
    # Mana-efficient maintenance above 75%; stronger recovery at/below 75%.
    if pet_health_pct(mob) > MAGERY_HEAL_SWITCH_PCT:
        return cast_heal_on_pet(mob)
    return cast_greater_heal_on_pet(mob)


def cast_arch_cure_on_pet(mob):
    return cast_magery_on_pet("Arch Cure", mob, ARCHCURE_CAST_DELAY)


def cast_secondary_heal(mob):
    if method_uses_magery():
        return cast_adaptive_magery_heal_on_pet(mob)
    return False


def cast_secondary_cure(mob):
    if method_uses_magery():
        return cast_arch_cure_on_pet(mob)
    return False


# -----------------------------
# HEAL LOGIC
# -----------------------------
def heal_logic(mob):
    vet_available = method_uses_vet() and vet_source_available()
    magery_available = method_uses_magery() and magery_source_available()
    secondary_available = magery_available
    double_heal_active = update_double_heal_mode(mob)

    if vet_available:
        update_poison_panic_tracking(mob)
    else:
        reset_poison_panic_tracking()

    damaged = pet_is_damaged(mob)
    poisoned = pet_is_poisoned(mob)

    if not damaged and not poisoned:
        reset_double_heal_mode()
        reset_poison_panic_tracking()
        return

    close_enough = in_bandage_range(mob)

    if method_uses_vet() and not secondary_available:
        if not vet_available:
            return
        if close_enough and (damaged or poisoned) and can_bandage():
            use_bandage_on_pet(mob)
        return

    if not vet_available:
        if poisoned:
            cast_secondary_cure(mob)
        elif damaged:
            cast_secondary_heal(mob)
        return

    if not close_enough:
        reset_poison_panic_tracking()

        if secondary_available:
            if poisoned:
                cast_secondary_cure(mob)
            elif damaged:
                cast_secondary_heal(mob)
        return

    if should_force_secondary_cure(mob) and secondary_available:
        if not cast_secondary_cure(mob):
            if can_bandage():
                use_bandage_on_pet(mob)
        return

    if poisoned:
        if can_bandage():
            use_bandage_on_pet(mob)
        return

    if double_heal_active and secondary_available:
        if last_lowhp_action == "spell":
            if can_bandage() and use_bandage_on_pet(mob):
                return
            cast_secondary_heal(mob)
        else:
            if not cast_secondary_heal(mob):
                if can_bandage():
                    use_bandage_on_pet(mob)
        return

    if can_bandage():
        use_bandage_on_pet(mob)


# -----------------------------
# STARTUP
# -----------------------------
heal_method = get_saved_heal_method()
double_heal_enabled = get_saved_behavior_setting("double_heal_enabled", True)
panic_cure_enabled = get_saved_behavior_setting("panic_cure_enabled", True)
transparency_enabled = get_saved_behavior_setting("transparency_enabled", False)
reset_resource_state()
load_saved_pet_without_prompt()
# Complete first-run migration from the previous Shared Values and ensure
# both current choices are durable before the main loop begins.
write_player_settings(pet_serial, heal_method)

# Open immediately. Never force a target cursor at startup.
draw_main_gump()


# -----------------------------
# MAIN LOOP
# -----------------------------
while Player.Connected and not main_gump_closed:
    handle_gumps()

    pet = get_pet()

    if not pet_exists(pet):
        reset_double_heal_mode()
        reset_poison_panic_tracking()

        if active_child_gump is None and should_redraw_main():
            draw_main_gump()

        Misc.Pause(LOOP_DELAY)
        continue

    refresh_resolved_pet_name(pet)

    if not healing_paused:
        heal_logic(pet)

    if active_child_gump is None and should_redraw_main():
        draw_main_gump()

    Misc.Pause(LOOP_DELAY)

close_all_petmedic_gumps()
