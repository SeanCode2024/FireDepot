from datetime import datetime, timedelta

def calculate_salary(start_time, end_time, basePay):
    # Convert times to datetime objects for calculations
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    # Ensure end time is after start time
    if end < start:
        end += timedelta(days=1)
        
    # Define daytime range (8 AM to 8 PM)
    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("20:00", "%H:%M")
    
    # Determine the hourly rate based on time of day
    day_rate_min = round((basePay / 2) / 60, 2)
    night_rate_min = round((basePay * 2) / 60 ,2 )
    
    day_first_hour = basePay
    night_first_hour = basePay * 2
    
    total_call_seconds = (end - start).total_seconds()  # Get the difference in seconds
    total_call_mins = int(total_call_seconds // 60) 
    
    # Define the ranges for day and night
    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("20:00", "%H:%M")
    
    
    # print('Day Rate Min =', day_rate_min)
    # print('Night Rate Min =', night_rate_min)
    # print('Total Mins =', total_call_mins)

    if start >= day_start and start <= day_end:
        # print('Day Shift')
        if total_call_mins <= 60:
            salary = day_first_hour
        else:
            first_hour = day_first_hour
            remaining_minutes = total_call_mins - 60
            salary_for_remaining_minutes = remaining_minutes * day_rate_min
            
            salary = first_hour + salary_for_remaining_minutes
    else:
        # print('Night Shift')
        if total_call_mins <= 60:
            salary = night_first_hour
        else:
            first_hour = night_first_hour
            remaining_minutes = total_call_mins - 60
            salary_for_remaining_minutes = remaining_minutes * night_rate_min
            
            salary = first_hour + salary_for_remaining_minutes
    return salary
            
    
    
start2 = "13:07"
end2 = "14:51"
base_rate = 49.54
print(calculate_salary(start2, end2, base_rate))  # Example 2
    
    