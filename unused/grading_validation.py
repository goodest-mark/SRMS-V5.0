def validate_rules(rules):
    """
    rules:
        [
            ("A",75,100),
            ("B",65,74),
            ...
        ]

    Returns:
        (True, "")
        (False, "reason")
    """

    covered = set()

    for grade, minimum, maximum in rules:

        if minimum > maximum:
            return False, f"{grade}: minimum is greater than maximum"

        for mark in range(minimum, maximum + 1):

            if mark in covered:
                return False, f"Mark {mark} appears twice"

            covered.add(mark)

    missing = [m for m in range(0,101) if m not in covered]

    if missing:
        return False, f"Missing marks: {missing}"

    return True, ""