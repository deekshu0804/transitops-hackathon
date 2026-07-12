from datetime import date

def can_dispatch_trip(vehicle, driver, cargo_weight: float):
    if vehicle.status != "available":
        return False, "Vehicle not available"
    if driver.status == "suspended":
        return False, "Driver suspended"
    if driver.status != "available":
        return False, "Driver not available"
    if driver.license_expiry_date < date.today():
        return False, "Driver license expired"
    if cargo_weight > vehicle.max_load_capacity:
        return False, "Cargo exceeds vehicle capacity"
    return True, None

def dispatch_trip(trip, vehicle, driver):
    trip.status = "dispatched"
    vehicle.status = "on_trip"
    driver.status = "on_trip"

def complete_trip(trip, vehicle, driver, final_odometer: float, fuel_consumed: float):
    trip.status = "completed"
    trip.actual_distance = final_odometer - vehicle.odometer
    trip.fuel_consumed = fuel_consumed
    vehicle.odometer = final_odometer
    vehicle.status = "available"
    driver.status = "available"

def cancel_trip(trip, vehicle, driver):
    trip.status = "cancelled"
    if vehicle.status == "on_trip":
        vehicle.status = "available"
    if driver.status == "on_trip":
        driver.status = "available"