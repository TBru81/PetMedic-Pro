# PetMedic Pro 2.1 Release Notes

PetMedic Pro 2.1 expands player control and introduces the UOAlive Script Suite's finalized transparent-gump standard while preserving the validated 2.0 healing engine and timing.

## New in 2.1

- Double Heal and Panic Cure can be enabled independently in Vet + Magery mode.
- Both behaviors remain enabled by default, preserving the established 2.0 behavior.
- Behavior choices are saved separately for each character.
- Double Heal and Panic Cure checkboxes appear only when Vet + Magery is selected; their labels and information buttons remain available in every healing mode.
- Adaptive Magery is identified as an automatic passive/background behavior.
- A per-character Transparent Gumps option applies immediately to the Main, Options, and information gumps.
- Transparent mode uses one continuous translucent surface and retains a compact title-area grab handle.
- Options spacing and information-button alignment follow the current Suite UI standard.

## Preserved healing behavior

- Double Heal retains the validated bandage and Greater Heal alternation, 50% activation threshold, and 75% recovery threshold.
- Panic Cure retains its emergency Arch Cure behavior when poison persists at 40% health or lower after two completed bandage attempts.
- Poison continues to take priority over Double Heal.
- Vet + Magery continues to switch automatically between Veterinary and Magery based on bandage range and bandage availability.
- Adaptive Magery continues to use Heal above 75% health and Greater Heal at 75% or lower.

## Validation

- All five RC1 production smoke checks passed.
- Double Heal was live-tested both enabled and disabled.
- Panic Cure was live-tested enabled; its rare disabled emergency path was code-verified.
- Saved pet, healing method, behavior choices, and Transparency setting were verified.
- Main, Options, and information gumps were verified in Transparency mode.
- Pause and Resume Healing were verified.

Validated for UOAlive with ClassicUO and Razor Enhanced.
