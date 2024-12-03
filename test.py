from datetime import datetime, timedelta

def calculate_salary(start_time: str, end_time: str, base_rate: float):
    # Parse the start and end times into datetime objects
    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')

    # Ensure the end time is after start time, if not, add a day
    if end < start:
        end += timedelta(days=1)

    # Initialize salary and current time tracking
    salary = 0.0
    current_time = start

    # Pay for the first hour
    if 8 <= current_time.hour < 20:
        # Daytime: pay full base rate for the first hour
        salary += base_rate
        current_time += timedelta(hours=1)
    else:
        # Nighttime: pay double the base rate for the first hour
        salary += base_rate * 2
        current_time += timedelta(hours=1)

    # Calculate remaining time after the first hour
    remaining_minutes = (end - current_time).seconds / 60

    if remaining_minutes > 0:
        if 8 <= current_time.hour < 20:
            # Daytime: pay half the base rate for the remaining minutes
            half_rate = base_rate / 2
            per_minute_rate = half_rate / 60
            
            print('half rate -', half_rate)
            print('Min Rate -', per_minute_rate)
        else:
            # Nighttime: pay double the base rate for the remaining minutes
            per_minute_rate = (base_rate * 2) / 60  # Nighttime pay is doubled per minute rate
            
            print('Min Rate -', per_minute_rate)
            print('Remaining minutes -', remaining_minutes)

        salary += per_minute_rate * remaining_minutes

    return round(salary, 2)

# Example usage:
start2 = "21:51"
end2 = "22:42"
base_rate = 49.54
print(calculate_salary(start2, end2, base_rate))  # Example 2
