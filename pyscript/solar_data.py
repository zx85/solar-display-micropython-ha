import json


@service
def get_solar_data():
    states = {}
    state_list = {
        "solar_in": "sensor.solis_ac_output_total_power",  # current solar power
        "power_used": "sensor.solis_total_consumption_power",  # current consumption
        "grid_in": "sensor.solis_power_grid_total_power",  # current grid power
        "battery_per": "sensor.solis_remaining_battery_capacity",  # % battery remaining
        "export_today": "sensor.solis_daily_on_grid_energy",  # exported today
        "solar_today": "sensor.solis_energy_today",  # solar today
        "grid_in_today": "sensor.solis_daily_grid_energy_purchased",
    }
    for state_label, state_name in state_list.items():
        states[state_label] = state.get(state_name)
    states["timestamp"] = state.getattr(sensor.solis_ac_output_total_power)[
        "Last updated"
    ]
    state.set("input_text.solar_display_data", value=states["timestamp"], info=states)
