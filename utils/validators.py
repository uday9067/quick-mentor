def validate_roll(roll):
    if not roll:
        return False, "Roll number is required."

    roll = roll.strip()

    # Must be exactly 5 digits
    if not roll.isdigit() or len(roll) != 5:
        return False, "Roll number must be exactly 5 digits."

    year = int(roll[:2])
    division = int(roll[2])
    roll_no = int(roll[3:])

    # Year check (basic sanity)
    if year < 20 or year > 30:
        return False, "Invalid admission year in roll number."

    # Division check (1–4)
    if division < 1 or division > 4:
        return False, "Invalid division. Must be between 1 and 4."

    # Roll number check (01–60)
    if roll_no < 1 or roll_no > 60:
        return False, "Invalid roll number. Must be between 01 and 60."

    return True, roll


def validate_password(password):
    if not password:
        return False, "Password is required."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    return True, password
