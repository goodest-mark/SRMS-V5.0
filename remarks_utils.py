def get_default_remark(average, division, level):
    """Generates a default teacher remark based on student performance."""
    if division == 'I':
        return "An excellent performance. Keep up the high standard."
    elif division == 'II':
        return "A very good performance. You have potential for even better results."
    elif division == 'III':
        return "A fair performance. Aim higher next time."
    elif division == 'IV':
        return "You have passed, but more effort is needed in weak subjects."
    elif division == '0':
        return "Performance is below average. Serious remedial work is required."
    
    try:
        avg = float(average)
    except (ValueError, TypeError):
        avg = 0

    if avg >= 80:
        return "Outstanding academic achievement."
    elif avg >= 70:
        return "Commendable performance. Keep it up."
    elif avg >= 60:
        return "Good performance. Can be improved with more effort."
    elif avg >= 50:
        return "Average performance. More focus is needed."
    elif avg > 0:
        return "Poor performance. Significant improvement required."
    
    return "No marks recorded for this period."

def get_headteacher_remark(division):
    """Generates a default headteacher remark."""
    if division == 'I':
        return "Excellent results. Keep it up."
    elif division == 'II':
        return "Very good work. Aim for Division I."
    elif division == 'III':
        return "Good attempt. Put in more effort."
    elif division == 'IV':
        return "Fair. Needs to work much harder."
    elif division == '0':
        return "Very poor. Must repeat or seek remedial help."
    return "Result pending."

def get_developmental_note(average):
    """Generates a default developmental note."""
    try:
        avg = float(average)
    except (ValueError, TypeError):
        avg = 0

    if avg >= 75:
        return "Consistently demonstrates a high level of understanding and skill."
    elif avg >= 50:
        return "Shows steady progress but needs to focus on consistency."
    elif avg > 0:
        return "Requires targeted support and more practice in key areas."
    return "Awaiting assessment results."
